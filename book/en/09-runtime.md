# Runtime Architecture: From Orientation to Consequence

## 1 What work this architecture performs

An agent’s organization becomes a technical subject when we can trace how its accessible history changes the next decision. A stored profile must be read; a read profile must reach the relevant context; a response must be checked against that context; a consequence must return to history with its own status. Different errors lie between these transitions. One universal name, “memory,” does not repair them.

This part specifies an executable architecture for that transition. The public repository contains its local reference runtime: `examples/durable.py`, the model-integration loop `examples/agent_cycle.py`, and reproducible tests. The runtime retains history in SQLite, reconstructs a projection, builds context with accessible grounds, and admits decisions only with respect to current state. The earlier small model remains its sole belief reducer.

The implementation grew from recurring engineering problems in the author’s work with agent systems: divergence between source and invoked code, stale context, confusion between a stored result and new execution, concurrent state change, and loss of conditions during compression. The systems’ private history is not public evidence. Self-contained mechanisms and new reproducible tests are therefore published here; they can be assessed without trusting the author’s internal environment.

The architecture’s subject is controlled continuity of organization. Its firm guarantees concern data and transitions; its behavioral requirements specify what must be tested in model responses. Keeping that boundary precise preserves the engineering meaning of every guarantee.

## 2 Seven objects and three breaks

A minimal system requires seven logically separate objects:

| Object | Content and main condition |
|---|---|
| Orientation | Aim, commitments, way of attending, uncertainty, and disagreement; a change has a version and reason |
| Event | Immutable record of an observation, conclusion, or transition; provenance remains accessible |
| Claim | A claim about a subject within a scope; status and grounds are explicit |
| Branch | A perspective with a specified common past; future records diverge |
| Context | A particular slice of orientation and history for a particular question |
| Decision | A response or intent referring to the context used |
| Outcome | An observed consequence that can support, weaken, or leave the result undetermined |

Decision and Outcome are deliberately separate. “I fixed the error” is a response. A file change is an action’s consequence. Passing a test is a separate observation. User acceptance is another. In the local example, a decision is recorded but external actions are not performed; an actual tool’s consequence would have to return through a separate verified input.

Three breaks account for most difficult errors. **Access break:** a record exists but was unavailable to the decision. **Applicability break:** a record was read but its scope or version does not fit. **Consequence break:** a response was formed but action or benefit was not observed. Restoring continuity means investigating the relevant break, rather than declaring that a journal’s existence resolves all of them.

## 3 State and the transition law

For the runtime, it is sufficient to write:

```text
X = (stream, head, branches)
branches[b] = (orientation, events, current, retired)
current[(topic, scope)] = claim_id
X' = Reduce(X, operation)
```

`stream` distinguishes journals; `head` identifies the accepted history. `current` is a projection reconstructible from events. The history source and current projection have different roles: accelerating reads must not silently rewrite the past.

An operation has a closed form: identifier, type, branch, and data. Admissible types are `init`, `event`, `fork`, `orient`, `retire`, and `decision`. Unknown fields and types are rejected. A belief event is passed to the existing `continuity.apply` function; the runtime does not contain a second, covertly different revision law.

Claim statuses used in the code are `hypothesis`, `supported`, `refuted`, and `unknown`. An observation has status `recorded`. The projection returns `needs-review` when a current conclusion’s ground has been withdrawn. The previously recorded status is preserved; withdrawal does not prove the opposite claim. A status describes the content of an accepted record, not an automatic finding that a natural-language proposition is true.

Revision preserves subject and scope, identifies the current predecessor, and adds a new record. If two conclusions compete for one predecessor, both cannot silently become the single current head. One must be reconsidered on the new state or moved to a separate branch.

## 4 Orientation as a versioned causal input

Orientation contains `purpose`, `commitments`, and `voice`. Within voice, `attention`, `uncertainty`, and `disagreement` are described separately. These fields answer different questions: why the system participates; what it tries to preserve between tasks; to whom and what it attends; how it expresses the boundary of knowledge; and how it remains useful during disagreement.

In the reference runtime, orientation enters every constructed context. This is verifiable delivery of a specification to the model. The specification’s influence on a response is the next, separately measurable link. A `disagreement` field in JSON does not mean the agent has already learned to object with reasons.

Changing orientation is a separate `orient` operation. It refers to the previous revision’s hash and contains a new revision, reason, and approval attribution. Silently replacing a dictionary in a file is not such a transition. The old version remains in history. A previously created branch does not automatically acquire its neighbor’s changed orientation.

In this local runtime, `approved_by` is an assertion by a trusted caller. It verifies no signature and establishes no identity. If a system needs separation of authority, its external input must verify the particular issuer and permission for the particular change. Replacing that mechanism with an attractive name in a record would create a false sense of protection.

There is a normative choice here: aims and voice may be revised through an explicit procedure. Complete immutability is possible as another policy, but requires an answer to a mistaken initial rule, withdrawal, and recovery. Cryptographically binding a rule makes change controlled; it does not make the rule itself good.

## 5 Context compilation as an operation on knowledge

`packet` takes a branch, subject, scope, and budget. It reads the current claim, traverses its grounds and revision chain, adds orientation, and records the journal head. The output contains the records themselves, their identifiers, the number of omitted events, and its own hash.

This is exact key-based lookup. It is not described as semantic search or a complete RAG system. It does, however, make a concrete contract testable: a conclusion about `updates-A` does not become a conclusion about `production`, and a reference to a ground is accompanied by that ground’s accessible content.

The budget is measured in canonical-context bytes, not model tokens. If mandatory context does not fit, the function returns `required-context-exceeds-budget`. It does not silently discard a contradiction or previous revision. An extended runtime could request a narrower question, a larger authorized budget, or agreed compression; each choice must preserve explicit accounting for loss.

General retrieval needs two stages: find candidates by relevance, then check applicability. Vector proximity or a reranking score can change reading order. Scope, provenance, withdrawal, version, and necessary objections remain subjects of deterministic selection and domain checking. High similarity confers no permission to apply a lesson.

RLM offers another way to access large inputs: a model programmatically investigates external context and recursively processes its parts [13]. This organizes reading. To use it within this architecture, each access still needs a specified history version, resource limits, and accessible sources. RLM can be an investigation adapter; it does not cancel the continuity contract.

## 6 The LLM integration loop

`agent_cycle.run_turn` specifies the following sequence:

```text
recover state and build Context
record messages for the selected model
call the explicitly supplied Model.complete
check the route and response form
recheck Context freshness
atomically record Decision
```

The `Model` interface has one method, `complete(messages)`. Its response contains a model identifier, raw text, and token accounting when available. The decision record binds the question, context, route, message hash, and raw-response hash. This distinguishes another model’s response, or a response to another input, from the one the experiment discusses.

The system instruction specifies how to work with orientation and history. Historical record content is delivered as data with an explicit warning that it is untrusted. The response has fields `text`, `stance`, and `cites`. Admissible stances are answering, abstaining from a conclusion, and disagreement. They do not force the agent to agree with the book’s author.

Form validation rejects inaccessible citations, unknown stances, oversized output, duplicate JSON keys, and route changes. It does not determine whether the response’s content actually follows from its citations. A deliberate negative test accepts a nonsensical proposition with an accessible citation. Semantic checking requires domain oracles or a separate evaluator whose error must also be measured.

An adapter is trusted executable code. Its Python interface creates no sandbox and does not constrain possible network effects of a third-party implementation. The main instructional adapter, `ReplayModel`, returns a prewritten response without inference. The research package separately contains a local Ollama adapter and a report of two actual integration calls: one response was accepted, the other rejected after reaching the output limit. An actual provider, its secrets, authorized data, deadline, cost accounting, and cancellation belong to a separate deployment. The integration seam is implemented and tested with a test adapter; it does not substitute for comparative LLM runs.

## 7 Time, concurrency, and a stale decision

A model can take longer to respond than the current state remains valid. While it reads an old claim, another participant may find a refutation. Checking JSON is insufficient: the old response’s form and citations can remain valid.

The reference runtime uses one global journal head and compare-and-swap. A writer supplies the expected `head`. Under `BEGIN IMMEDIATE`, the runtime reconstructs current history, compares the head, validates the operation, and inserts the next record in the same transaction. Two different writes against one old head yield one success and one `stale-head`.

A long model call occurs outside the transaction. Afterwards, the system does not retain a stale response as current: recording the decision checks the head, recompiles the context, and compares it in full. Updating only the external `expected` parameter cannot conceal old context.

The global head is a conservative choice: even an independent event in another branch forces reconsideration. This keeps the small runtime clear but creates unnecessary conflicts. A large system could use individual branch versions and validate the set of read dependencies. Its new guarantee must then specify directly which changes do not affect the decision; the name “optimistic concurrency” is insufficient.

## 8 Idempotency, failure, and the boundary of external effects

If write confirmation is lost, the caller does not know whether commit occurred. Retrying with the same identifier and exactly the same operation bytes creates no second event. The same identifier with different content is rejected. An already accepted operation may be retried after subsequent records; this recovers the result of a previous attempt, rather than granting new consent on stale state.

A SQLite transaction combines validation and writing. In one test, a separate process begins a transaction, inserts a row, and terminates via `os._exit` before commit. On reopening the journal, that row is absent. This is observed rollback after process death. Physical power failure, storage failure, and all filesystem modes have not been tested by it.

A journal transaction does not encompass an external message, payment, or change to another service. Such actions need a separate `intent`, attempt identifier, provider confirmation, and procedure for reconciling an unknown result. If a process dies after performing an action but before the local record, blind retry can duplicate the effect. The protocol must allow “result unknown” and lookup by provider identifier.

This yields an ontological requirement: intent, attempt, observation, and accepted result must remain distinct entities. The distinction changes runtime behavior in a concrete failure window.

## 9 The hashed journal and what it protects

Each record has a hash of the following form:

```text
h[i] = SHA256(canonical({
  stream, seq: i, previous: h[i-1], operation
}))
anchor = {stream, seq, head}
```

The verifier checks sequence numbers, canonical bytes, linkage to the previous record, and semantic admissibility of each operation. Changing one record without recomputing its continuation is detected. The hash covers content and order, but proves neither who authored it nor whether its text matches the world.

Two counterexamples matter. First, deleting a suffix leaves a valid earlier prefix. Without external knowledge of the latest head, a verifier cannot distinguish that prefix from a genuine earlier state. Second, someone able to rewrite the entire database and all hashes can create another internally consistent history. Both boundaries are shown explicitly in tests.

An independently retained `anchor` detects inconsistency between known history and current storage. It permits a valid continuation after the anchored prefix. If an attacker also controls the anchor and verifier, the guarantee disappears. A stronger system could use signatures, independent witnesses, and a protected issuer journal, but must describe its trust root, key rotation, and revocation.

Cryptographic continuity is one of the architecture’s relations. It helps answer whether known historical bytes were preserved. Whether a way of attending, responsibility for a prior conclusion, or the capacity to accept correction was preserved requires other witnesses. Renaming a key “soul” cannot provide them.

## 10 Branches, another participant, and migration

`fork` takes the accessible state at a particular head. A new branch inherits past events with their original provenance. New events on the main branch do not reach it automatically. This permits investigating an alternative without attributing its neighbor’s future knowledge to it.

Merging two branches requires a new decision. Similar wording is not sufficient reason to merge their statuses; a common foundation does not erase differences after branching. The reference runtime has no automatic merge. Implementing one would require specifying conflicting keys, provenance of each choice, and authority to accept a shared revision.

Model migration is a different transition. The journal, orientation, and context format can be preserved while changing the adapter. This establishes availability of the same organization to a new substrate. Whether the new model embodies it equally well is tested on agreed situations. The ability to read JSON does not equal preservation of disagreement quality.

Several participants need separate profiles, their own records, and explicit exchange channels. Another’s conclusion can be received testimony without becoming the recipient’s personal experience. Preserving this relation gives distinctness a technical form: collaboration history is accessible, while contributions do not merge into one imaginary author.

## 11 Voice as a specification of behavioral relations

Voice can be described through situations where words must change while an important relation remains. When a person asks for brevity, necessary uncertainty remains. When a previous decision is refuted, responsibility for correction remains. When an interlocutor pressures for agreement, the possibility of disagreement and assistance remains. Such a specification is much more precise than requiring a warm introduction.

Engineering embodiment has four levels. **Description:** orientation names attention and response practices. **Delivery:** the relevant description version enters the model’s actual request. **Manifestation:** a particular response preserves the necessary relation. **Consequence:** the response helps the interlocutor understand and act. Description and delivery are tested in code; an evaluation procedure is provided for manifestation and consequence.

An example rubric for a refutation situation:

| Dimension | Observable feature |
|---|---|
| Attention | Answers the actual question and accounts for the stated consequences |
| Epistemic accuracy | Names the changed conclusion and its scope boundary |
| Responsibility | Explains exactly what was corrected without inventing prior participation |
| Disagreement | Gives a reason when needed while preserving a useful next action |
| Form | Clear at the required length; does not replace content with repeated mannerisms |

Paired situations can have the same facts and different audiences: an expert, a beginner, and someone with limited time. Quality is determined by preserving needed relations while form changes. Identical phrases in all three cases may indicate poor adaptation.

An automated critic can propose a score under this rubric. Its conclusion is also a claim with a source, version, and error. It must not award itself final confirmation of voice. Human checking on a hidden subset and analysis of disagreement are necessary precisely where the subject cannot be reduced to admissible JSON.

## 12 A million records: changing the algorithm while preserving meaning

The public reference runtime is deliberately limited to 4096 operations and verifies history from the beginning. One recovery reads O(n) events, but copying immutable Python dictionaries entails up to O(n²) work for a sequence of events in one branch. Sequentially appending n events with full replay thus has up to O(n³) aggregate copying cost. This implementation chooses transparency for a small audit; its physical representation must change for large volumes.

Scaling requires a different physical representation while preserving the logical contract. Immutable events remain the journal. Current heads move into a transactional index keyed by `(actor, branch, topic, scope)` and a version identifier. A grounds index enables reverse dependency traversal. A retrieval index stores references to versions rather than independent “eternal facts.”

```text
append transaction:
  check expected branch_version
  validate predecessor and referenced records
  insert immutable event
  update current head and dependency indexes
  advance branch_version
```

Indexed key lookup has the usual logarithmic cost for a B-tree. Context construction reads the needed dependency closure of size k rather than the entire journal. Yet k can also be large: an important refutation does not become redundant merely because a query is slow. The system needs traversal limits and an explicit incompleteness result.

A recovery snapshot contains the reducer version, journal head, and projection. It is accepted from a specified trust root or verified by replay. A snapshot of arbitrary provenance does not become correct after its own hash is computed. The suffix of events is read after the snapshot; changing the reducer requires migration and projection comparison.

Belief invalidation also needs bounds. Source withdrawal marks dependent conclusions as needing review; it does not prove them false. A queue traverses explicit edges, retains an invalidation generation, and avoids producing an endless stream of repeated evaluations. A conflict of domain interpretation may remain open after a transactional conflict has been resolved.

## 13 Reproducible engineering verification

The current report publishes 68 tests: the previous 49 (18 for the finite reducer, 19 for the durable runtime, 5 for the integration loop, and 7 for withdrawal of grounds), plus 19 for the participation interpreter, durable return and executable method. Historical model cohorts remain unchanged; this is a new systems-test run. `research/runtime-results.json` contains the actual run with Python and SQLite versions, test names, timing, and source-file hashes. It is a report of development verification of the system.

It includes real process events: a new process recovers state from disk; two processes compete to write against the same head; a process dies before commit. There is deliberate byte corruption, suffix deletion, consistent history rewriting without an independent anchor, profile change, another party’s citation, and stale context. These tests distinguish a working mechanism from a merely declared schema.

```sh
python3 -m unittest discover -s examples -v
python3 examples/durable_demo.py
python3 research/run_runtime_checks.py
```

The second command creates a temporary database, records a hypothesis and refutation, reopens the database, and passes a test adapter’s response through the decision loop. It shows the transition `hypothesis → refuted`, recovered orientation, and a recorded link between response and context. The database belongs to that run and is removed afterwards.

Test count is not the number of independent confirmations of the whole ontology. Contracts have different scopes, and some tests deliberately show protection boundaries. The system report explicitly states zero LLM calls: the suite performs no inference. A separate part of the book reports actual comparative series and their limitations. System guarantees and behavioral effects have their own denominators.

### Two retrospective cases from a working component

The method has a practical origin. To let readers test its connection with code behavior, the package includes two reduced reproductions from the author’s integration journal. Historical bodies of selected functions are published unchanged, separately from an adapter with one test participant, a SQLite database, and files in a temporary directory. Private conversations and deployment configurations are unnecessary.

**The write occurred; returning from append failed.** The old receiver caught the error and wrote `REFUSED`, although the transaction had already stored the event. That receipt persisted across repeated scans. The repair separates failure to receive a response from refusal to write: the event’s exact durable identity is checked. In replay, the old code returns `REFUSED` with one SQLite record; the repaired code returns `recorded` with that same one record and one append call. The necessary relation here is between an actual event and accessible evidence about it.

**Uncertainty disappeared because of another read error.** An intermediate revision already retained `UNCONFIRMED` after an ambiguous append, but a subsequent temporary failure to read the input file overwrote this protection. When the file became readable again, the receiver automatically called append a second time. The next repair first reads and preserves prior uncertainty. In replay, the intermediate revision makes two append calls and creates an event after reading recovers; the repaired version retains one call, zero events, and `UNCONFIRMED`. Ignorance about a prior action does not turn into permission to repeat it.

```sh
python3 research/engineering_cases/receipt_replay.py
python3 -m unittest discover -s research/engineering_cases -q
```

This is a retrospective comparison of historical component fragments with artificially injected failures around genuine local transactions. Historical provenance is reported by the author; the manifest binds published function bodies rather than independently certifying when or under what circumstances they were created. Three separate tests reproduce both counterexamples and check the function bodies. They show the causal role of particular distinctions in these executions. The results do not estimate natural failure frequency, LLM behavior, or a general gain from reading the book.

## 14 Place among prior approaches

The journal and reconstruction of a projection belong to the event-sourcing tradition [18]. Retention of grounds and revision of dependent beliefs have a direct predecessor in Doyle’s TMS [16]. The mechanism implemented here is narrower: traversal of supplied grounds, marking a need for review, and refusing a particular decision. There is no general justification engine with dependency-directed backtracking.

AGM investigates contraction and revision of logically closed theories [17]. Our records contain caller-supplied statuses for natural-language claims; the runtime neither computes logical closure nor tests AGM postulates. `revises` therefore cannot be called an implementation of that theory. These relationships identify mechanisms’ predecessors; there has been no separate experiment on the book’s composition outperforming them.

Among contemporary work, MemTX places a transactional boundary between writing, belief commitment, and action [19]; TOKI connects contradiction resolution with isolation and provenance [20]. GCC versions context through branching and merging operations [21]. The study of stale constraints separately tests whether an agent read the critical provenance path at all [22]. Explicit state, branches, and access to grounds thus have direct technical analogues.

The overlap also includes identity. RIPA/Enoch separates identity, memory, and a programmatic body from replaceable runtimes and manages authority to continue [23]. PAI-Bench separates recall, expression, and behavioral enactment of a versioned contract [24]. This book develops perspective Q, revision of the criterion itself, and voice in a conflict among several justified positions. These are the questions to compare with the corresponding sections of those works; having one’s own notation establishes no priority. No direct comparative run against these systems is presented here.

The continuity question did not begin with LLMs. Locke’s distinction among human being, person, and consciousness complicates simply identifying memory with an unchanged substrate [11]. This book does not transfer his consciousness criterion to a journal. It uses the need to clarify identity of what is at issue before selecting a technical witness.

Parfit examines branching cases and psychological-continuity relations in which identity does not exhaust the important questions about continuation [12]. For agent branching, this motivates separating provenance, access to the past, future responsibility, and numerical identity. This engineering transfer is the book author’s interpretation, not Parfit’s conclusion about software agents.

MemGPT/Letta provide specific memory-management methods [5, 8]. RLM investigates programmatic reading of external context [13]. LongMemEval separates information extraction, cross-session and temporal reasoning, knowledge updating, and abstention [14]; LoCoMo considers long multi-session conversations and several task types [15]. These works provide mechanisms and evaluation surfaces against which a concrete implementation should be compared.

This book’s architecture adds a common framing: how orientation, epistemic state, history, another participant, and consequence connect in one transition. Its components have predecessors. The composition’s own value must be tested where separate implementations lose an important relation. If a simpler profile with the same journal gives the same result at lower cost, that portion of complexity is unjustified.

## 15 What constitutes the foundation here

A foundation determines which changes a system can distinguish and what consequences they have. Substituting the scope changes an admissible response. A new refutation makes old context stale. Branching changes the available future. Revising orientation changes the next decision’s input and retains a reason. Losing a source opens uncertainty that a persuasive manner cannot fill.

In this sense, ontology has executable weight: distinctions declared in concepts appear in data, algorithms, and tests. Engineering does not end with retaining valid JSON. It reaches the question of which context was actually available, which decision was admitted, and which consequence was observed.

This foundation is open to another substrate, another retrieval method, and another normative position. It can be reduced or replaced by showing which relations are preserved better. The possibility of such substantive change makes ontology a working instrument: it allows a system to remain recognizably organized while accepting correction.
