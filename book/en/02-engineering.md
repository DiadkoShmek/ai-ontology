# Engineering Embodiment

## 1 From a question to a mechanism

Engineering implementation begins with a question the system must answer. For example: “what ground changed this belief?”, “what was carried across the interruption?”, or “was the way of explaining disagreement preserved?” Questions of this kind identify the necessary entities and relations. In ontology engineering, they help delimit a model’s domain and evaluate its suitability [1].

For this book, the distinction between a conceptual model and a formal ontology in a particular language matters. OWL 2 provides classes, properties, and formal semantics [2]. The present text offers a conceptual model and fragments of contracts; it is not a ready-made OWL ontology, a provably complete specification, or an interoperability standard. This is open engineering work for which different formalizations can be built.

One possible implementation is described below. It uses ordinary storage, an event journal, and a separate context builder. A graph database, vector index, or specialized platform may be useful when queries and load require them. Their use alone adds no ontological depth.

## 2 Before a claim is formalized

In a journal, an event already has a subject, scope, and status. Before that, someone transformed received material into such a record. This transition determines which error the runtime may subsequently preserve impeccably.

The message “after the update I see the old name again” permits recording that a certain participant reported this result. It does not yet establish that the server accepted the update, the intended document version was opened, or the cache caused the issue. Missing details should not be filled with typed fields carrying feigned certainty.

A working analysis should separate several questions:

| Subject | What needs to be established |
|---|---|
| Received material | What text, measurement, or file is available, and how was it obtained? |
| Claim | What exactly does the material permit us to assert? |
| Scope | Which versions, conditions, and times does the conclusion concern? |
| Alternatives | What other explanations fit this same material? |
| Next check | Which available action will distinguish the material explanations? |

For example, a stale cache and opening another version can explain the same complaint. A check must yield different expectations for these explanations: compare the version identifier and direct-read result with what search shows. If the necessary data is unavailable, what remains is a report with an undetermined cause. A new experiment on an authorized document investigates the mechanism under its own conditions; it does not itself recover the cause of a past event.

Provenance also requires interpretation: a message’s author may be recounting someone else’s execution. The right to report a result does not imply authority to approve a rule. The source’s relation to a claim, the source’s own reliability, and authority to act are different questions.

This is a procedure for establishing knowledge that allows human or model judgment and subsequent refutation. The book’s public runtime does not automate this analysis. It accepts already formalized records from a trusted caller; a negative test shows that a semantically false reference can pass structural validation. Before storage, the grounds for interpretation, an alternative, and the gap should therefore remain visible. Adding these records does not itself guarantee a correct interpretation.

## 3 Four planes

**The orientation plane** contains purpose, a commitment profile, voice, and rules for revising them. It answers which distinctions the system should preserve. Its records have revisions and authorship; the current role refers to them rather than silently rewriting the entire profile.

**The history plane** contains events, claims, results, and the provenance of changes. It distinguishes an observation, another party’s proposal, an accepted conclusion, and a superseded version. The journal can supply several projections: current beliefs, episodes, and a short session continuation. PROV-O provides a useful vocabulary of entities, activities, agents, and provenance relations [6]. A particular identity model remains a separate layer above that vocabulary.

**The participation plane** assembles relevant context and forms a decision. LLMs, retrieval, tools, and an arbitration mechanism operate here. This is where the relation between accessible history and a particular response must become evident. A message saying a profile was loaded does not yet show that manifestation.

**The observation and revision plane** compares expected and actual outcomes, detects breaks, and prepares candidates for change. It preserves negative results and side effects. Accepting a candidate is a separate transition; the self-report “I learned” does not replace it.

The planes are logical responsibilities, not a requirement to create four services. For a small system, one process and one transactional database may provide them more simply. The distinction prevents provenance, current decision, and outcome assessment from dissolving into one text.

## 4 Minimal entities

| Entity | Minimally important content | Query |
|---|---|---|
| Profile | Revision, purpose, commitments, voice | Which revision did the session receive? |
| Session | Identifier, environment, parent snapshot | From where does it continue the work? |
| Event | Type, source, recording time, data | What actually arrived? |
| Claim | Content, scope, status, grounds | Where and why does it hold? |
| Revision | Predecessor, change, reason, acceptance | What was revised, and by whom? |
| Relationship | Participants, agreement, scope | What has been preserved between them? |
| Episode | Question, choice, consequence, limit of the lesson | What can be reused? |

An event’s time and its recording time can differ. A late report of an old result should not automatically become the latest true state merely because of its arrival time. Likewise, a newer text may quote a previously refuted claim. Arrival order, causal order, and order of validity require separate semantics.

For a claim, at least two independent fields are useful: **epistemic status** and **application status**. A hypothesis can be available for analysis without being an accepted fact. A current rule may rely on an assumption that has just become doubtful; this opens revision of the rule. A single “active” flag hides these distinctions.

## 5 Memory as preparation for the next decision

Storage should support at least three operations: find relevant material, check its provenance, and assemble a usable continuation. Vector similarity assists the first. It does not establish that a retrieved record is current, belongs to the intended trajectory, or supports a new conclusion. Retrieval must be followed by metadata and content checks.

Stored profile blocks, such as those described in Letta’s documentation, keep part of the context continuously available [5]. Hierarchical memory management in MemGPT investigates moving information between a limited context and external memory [8]. These mechanisms address different questions of access. Neither determines by itself what the system should regard as its own history.

A context package for a new session can contain the current profile revision, current question, a few necessary claims, unresolved disagreement, and known gaps. Every element has a reason for inclusion. Full history is not always more useful: it consumes resources and may obscure the relevant passage. Lost in the Middle shows how results for certain models and tasks depend on the position of necessary information [9]. This motivates testing one’s own composition without establishing a universal rule for all contemporary models.

The context builder should return both the package and a list of what was omitted because of budget or lack of access. This list can be brief: “the primary journal is unavailable; the summary from revision 4 was used.” It does not restore what is lost, but prevents an impression of complete visibility.

## 6 Self-model and voice

It is useful to assemble a self-model from several sources: a declared profile, known configuration, observed capabilities, and error history. These sources have different statuses. The statement “I have tool X” may match the configuration without proving that X is available in this run. Historical success shows a capability under certain conditions; it gives no guarantee for an arbitrary task.

Voice is embodied in situational rules and examples. Under uncertainty, a profile might require beginning with the question’s exact state, explaining its boundary, and proposing a check. After an error, it might require naming the changed conclusion and practical consequence. This describes desired behavior that still needs testing in actual responses.

A separate form editor is possible, but risks changing meaning. For example, an initial conclusion of “insufficient data” becomes “almost certainly yes” for a decisive tone. Voice assessment must therefore cover preservation of modality, grounds, and open questions. Response pleasantness should be measured separately from accuracy. Research on sycophancy shows why human preference for persuasive text can conflict with truthfulness under the studied conditions [10].

Two good voices may differ in which loss they investigate first. One begins with the smallest action that will produce new knowledge; the other begins with the condition under which a decision will no longer be verifiable. On the same facts they may propose different work orders while both preserving accuracy. Individuality should be described through such choices, with examples of changing one’s position. Always placing one priority first would turn voice into an inflexible role.

## 7 The transition after an error

Consider the sequence: event → interpretation → revision candidate → test → acceptance → new projection. Every step may end in uncertainty. An event may be incomplete. An interpretation may have several alternatives. A candidate may fix one defect and introduce another. Rejecting a candidate is a fully valid result.

For a recurring software error, a candidate may become a test and a local fix. An unsuccessful interaction requires examples, human evaluation, and checks of neighboring situations. Verbal reflection, as in Reflexion, offers one way to carry feedback into later attempts without changing weights [4]. Its particular research results should not be generalized to every long-term system of relationships.

A candidate should specify its scope. “This case lacked a journal” does not yield the rule “never trust any summary.” Recovery from error requires control over the scale of generalization. This is where memory engineering meets character engineering: what the system does with failure becomes part of its subsequent way of participating.

## 8 Integrity under parallel load

Two sessions can revise the same profile simultaneously. If both write “revision 5,” one change may disappear unnoticed. A concrete implementation needs serialized writing or a check of the expected predecessor before acceptance. A conflict should return as a conflict so the new revision can account for both contributions.

Event redelivery also needs semantics. The same identifier with the same content can be handled as a duplicate; with different content, as a contradiction. This provides deterministic accounting but does not authenticate the source. Source and trust require a separate environmental model.

If the journal is updated but the current projection is not saved, the next reader may see old state. A transactional database or reconstruction of the projection from a consistent snapshot solves this specific visibility problem. Calling such storage “memory” does not change its correctness requirements.

## 9 A matrix of breaks

| Break | Observable symptom | Nearest check |
|---|---|---|
| A record exists but was not read | The session missed a necessary condition | Composition of the context actually delivered |
| A source exists but the conclusion is false | The reference does not support the claim | Semantic reading of the primary data |
| A profile exists but behavior differs | Voice disappears in conflict | New situations of disagreement and error |
| A revision lost a contribution | Two changes have the same predecessor | Concurrent writing and version conflict |
| Reflection became dogma | A local lesson blocks other tasks | Negative and neighboring cases |
| A collective lost its differences | The summary concealed an alternative | Provenance of contributions and reason for choosing |

## 10 The cost of organization

Every layer has a cost: profile tokens, retrieval, verification latency, storage, human attention, and maintenance. An architecture is justified when its contribution serves the purpose. A simple request may be better for a one-off text transformation. During months of research collaboration, the same economy can create substantial recovery losses.

Evaluation should therefore compare outcomes under agreed constraints, rather than component counts. Did particular errors decrease? Was response quality preserved? Did every action acquire an unnecessary ritual? Can a component be removed without regression? A negative answer also shapes the architecture.

The smallest suitable implementation may consist of a versioned profile, a few typed episodes, and an explicit revision procedure. Scaling should respond to an observed break. Ontology helps identify the necessary relation; it does not require deploying every possible piece of infrastructure.

## 11 A formal map and the actual runtime

In `ontology/`, this account receives a finite machine-readable profile: 18 classes, 34 relations and eight explicit questions about a record. Actor, model, profile and session have different types. Criterion acceptance, assessment under that criterion and permission to act have separate relations. Evidence does not become used merely by appearing in context. A stored lesson does not establish changed judgment without subsequent observation.

Definitions, fields, relation domains and ranges are specified in `vocabulary.json`; JSON-LD and Turtle are generated from that same source. The PROV-O mapping concerns provenance. It does not equate a software participant with a person. The executable validator checks a bounded record, not arbitrary world truth; it implements no general OWL or SHACL reasoning.

This is also connected to an actual runtime. `runtime_adapter.py` reads the actual world of the `examples/participation.py` interpreter and the real readback of its SQLite journal. Source fields remain preserved, unknown authorship and session stay unknown, and empty or rejected turns receive no invented effect. A test commits, closes, reopens and checks the projection.

The stronger `returnPath` query requires explicit links among an effect, observation, assessment, accepted revision and a consuming decision. The current runtime records the actual return dataflow, but does not attest that a particular assessment was the basis of a model revision. The adapter may therefore show an incomplete path even after a successful local action. It does not fill the missing link from an eloquent model explanation. A separate authored positive example illustrates the required structure while retaining its distinction from an observed fact.

This makes the ontology challengeable: one can identify a distinction it cannot represent, an invalid query inference or a simpler structure with the same discriminating capacity. A vocabulary's existence does not establish improvement; it makes the next experimental question more precise.
