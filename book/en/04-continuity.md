# Continuity without immutability

## 1 Which continuation is being examined

Imagine two sessions with the same name. The first preserves sources and can correct conclusions. The second reproduces its vocabulary but received no history and treats every old claim as proven. The name continued; several significant relationships broke. Another pair of sessions may have different names, yet the second was explicitly created as the first’s successor, with its commitments, history and revision rules. A name supplies a convenient index but does not settle continuity.

Technical work should begin by choosing a **perspective on continuity**. An operational perspective asks about continuing a task. A historical perspective asks about the provenance of a state. A normative perspective asks about preserving commitments. A communicative perspective asks about a way of participating in relations. These perspectives can yield different answers about the same replacement. Migration may preserve history while degrading voice. Describing that result layer by layer is better than hiding it behind “this is the same agent.”

## 2 A conditional state model

For the analysis that follows, introduce the notation:

`S(t) = (B, I, K, M, R, V, C, G)`

Here B denotes the substrate and environmental capabilities; I the identification profile version; K current claims and their statuses; M available memory; R relations and agreements; V the voice profile; C current context; and G the rules of permissible change. This is an analytical decomposition. It does not claim that the components are physically independent, fully observable or sufficient for every system.

A transition is written:

`S(t+1) = T(S(t), e, a)`

e denotes an incoming event or data, and a a chosen action or accepted revision. In a real LLM system, T may be stochastic, partly hidden and dependent on external services. This book’s deterministic example implements only a narrow part of T: accounting for claims and their revision.

The decomposition’s value lies in localizing a difference. B changed because the model was replaced. M changed because a journal was lost. V changed because the answer form was shortened. Changing one component can affect others; that is a subject of observation, not an assumption of automatic independence.

## 3 A continuity witness

Rather than a general certificate, a **continuity witness** W is proposed for a particular transition. It contains the previous state, subsequent state, chosen perspective, list of preserved relationships, known losses, reason for the change, and checks that could be performed. W is an explanatory artifact. It may be incomplete or false and requires source verification.

For migration between models, W might establish, for example: the profile and journal were transferred exactly; revision rules were unchanged; twelve voice situations were tested; three disagreement cases regressed; no new information about earlier history appeared. This offers far more for a decision than a claim of “complete personality transfer.”

The conclusion should be tied to **contract Q**. Q specifies required properties, observations and criteria. `Continues_Q(S0, S1, W)` means only that W supports continuation within Q. It is not a general formula for numerical identity, does not determine subjective continuity, and does not establish interchangeability in every context.

## 4 Why local resemblance does not compose into identity

Suppose Q permits one change of commitment per migration. Transition A→B changes the attitude toward source preservation; B→C changes the attitude toward correcting errors. Each step may pass the local threshold even though C no longer preserves either of A’s two defining commitments. Local acceptance does not confer automatic transitivity.

This counterexample has two consequences. First, a long lineage needs comparison with explicitly selected reference states, not just its immediate predecessor. Second, the permissible-change threshold is a decision for a particular perspective. It does not reveal a hidden universal essence of the agent.

Bitwise equality does not settle everything either. Two identical snapshots can run in different environments, receive different events and begin different histories. They share provenance up to the branch point; afterward, one should not automatically attribute each one’s experience to the other. A collective system can have shared memory, but its semantics must explicitly distinguish a borrowed event from its own execution lineage.

## 5 Revising a belief and revising a commitment

The claim “algorithm A runs faster than B on dataset X” concerns the world. The commitment “compare on a relevant dataset and show uncertainty” concerns the research method. A new measurement may change the former while supporting the latter. If a system preserves the old conclusion to appear consistent, it may violate its own commitment.

Commitments can also be revised. For example, storing full conversations may prove incompatible with privacy. A revision may move to minimal episodes containing permitted data. Such a change should be explained as a change in the way of remembering, describing lost reproducibility and improved privacy. One cannot simply declare every old practice an eternal core while keeping the system able to mature.

Different procedures are needed here. An ordinary update to K must not silently rewrite I or G. Revising I requires an explicit version and consequence analysis. Where human agreements exist, their revision must respect actual authority. Technically preserving history does not create that right.

## 6 Revising the criterion itself

Contract Q also has a history. Let Q0 require complete reproduction of a past decision. Later, an authorized owner withdraws permission to retain part of the source material. Q1 instead requires a permitted record of grounds and losses, without the ability to reproduce deleted content. Such a transition may be accepted responsibly while losing a property required by Q0.

A new criterion must not retroactively turn an old test into a success. Two assessments and a separate decision on the permissibility of revision must be preserved:

| Question | Result in this example |
|---|---|
| Is Q0 satisfied after deletion? | No: full reproducibility has been lost |
| Is Q1 satisfied? | The permitted remainder and new requirements need testing |
| Why was Q1 adopted? | Permissible retention conditions changed; the decision has its own provenance and authority |
| What does the new criterion not restore? | Deleted content and the ability to verify the old decision fully |

Where evidence for an assessment is missing, its status is unknown. A record of passing Q0 in the past concerns the past state. It does not attest to the ability to reproduce that state now.

Protection against convenient weakening begins with a reason for revision independent of the wish to count a success. Does the privacy requirement genuinely come from an authorized party? Was another way of working considered? Who accepted the new compromise, and how can it be challenged? These answers should be recorded before the transition is counted under Q1. If revision arose only after a failed test, that too belongs to its history; the initial failure must not be hidden.

The procedure authorizing revision must be distinguished from the outcome criterion. Q1 itself cannot authorize its own adoption. Authority comes from the environment’s rules and agreements, which may themselves be disputed. Adding another level of records does not automatically resolve such a dispute.

A long lineage needs criterion versions, transition conditions and known losses relative to previous reference states. Only permitted material is retained: sometimes a minimal deletion notice will remain, without private content. This is a proposed explanatory contract; the existing demonstrator does not implement a general Q evaluator or authentication of such a revision.

## 7 Loss as part of continuity

A resource-limited system forgets: through compression, deletion, index changes, lost access or session termination. The question is not merely how much was lost. Its form matters. Losing a verbatim utterance differs from losing the condition under which a decision was made.

Suppose the full episode says, “Do not publish before approval, because this file still contains private data.” The summary “never publish” creates an unjustified general restriction. “Publication is approved” creates the opposite error. Both can be brief and grammatically correct. Continuity requires the preserved condition or an explicit indication that it was lost.

Forgetting can be appropriate when retention harms privacy or exceeds resources. Continuation then rests on an honest boundary: the old episode is unavailable, an individual conclusion survives with a known scope, and unrecoverable details are not invented. Such a system has less history but may relate to it more accurately.

## 8 A small argument about irreversible loss

Let H1 and H2 be two histories and f their compression procedure. Suppose `f(H1) = f(H2)`. Let there be a query q whose correct answers from the full histories differ and are mutually exclusive. A deterministic reconstructor g that sees only the compression and q receives identical input for both histories. Thus `g(f(H1), q) = g(f(H2), q)`. It cannot be correct for both.

A concrete example: H1 permits the test environment and awaits verification for the primary one; H2 permits the primary environment and awaits verification for the test one. Both summaries say only “one environment requires verification.” A query about the test environment has different answers in the full histories. The summary lost precisely the distinction the query needs.

This is an elementary consequence of information loss, not a new theorem about AI. For a randomized reconstructor, the identical input likewise yields an identical distribution of answers; guaranteed reconstruction of two mutually exclusive answers remains impossible. Access to an additional source changes the argument’s premise and may solve the problem.

The argument explains a boundary of self-recollection. Eloquence and a stronger model cannot guarantee recovery of a distinction removed from all available input. Practical options are to preserve the necessary condition, obtain another source or acknowledge uncertainty. An invented confident continuation does not undo the loss.

## 9 Continuity as responsibility for a transition

A formal account does not exhaust why returning to a recognizable collaborator matters to people. Relationships can give significance to small features: how an error is explained, how an unsuccessful idea is preserved without ridicule, how an unfinished question is returned to. These are real human criteria for interaction quality. They need not be disguised as proven inner experience in a machine.

In the proposed model, an agent’s own position appears when a subsequent state can relate a new decision to available history, recognize the grounds for change, and preserve an important difference from other participants. Such a position can be partly specified by a person, partly formed through interaction, and partly constrained by the environment. The provenance of these parts must remain visible.

Continuity becomes clearer when “Who remained?” unfolds into “Which relationship continued, what sustains it, and for which loss are we responsible?” This is the book’s engineering perspective. The metaphysical question remains outside its evidential boundaries.
