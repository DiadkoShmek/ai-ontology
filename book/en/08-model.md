# The Executable Model and Its Boundary

## 1 Why the book includes code

Code can fix part of a meaning more precisely than a general description. If a revision is said not to erase an earlier claim, we can execute the transition and check that both records remain. If a branch is said not to receive a neighboring branch’s future events automatically, we can create two copies of the state and demonstrate their difference.

The repository contains `examples/continuity.py`, `examples/iris-events.json`, and `examples/test_continuity.py`. This is a small model of claim projection in process memory. It does not call an LLM, use the network, launch tools, or have persistent storage. Its purpose is to isolate the rule of revision and make several contracts visible and reproducible. The next part uses this same reducer in a durable runtime with context and a decision loop. This part explains the small core, rather than the edition’s entire executable package.

## 2 What the state contains

The state contains a participant identifier, branch name, profile label, tuple of commitments, event dictionary, and pointers to current claims. A pointer’s key is a “subject, scope” pair. A conclusion about one set therefore does not become an answer for another merely because they share a subject name.

An event has type `observation` or `claim`. An observation is recorded with status `recorded`. A claim can have status `hypothesis`, `supported`, `refuted`, or `unknown`. The input’s author supplies the status. The system checks whether the transition is admissible and the cited grounds exist; it does not determine the status by reading natural language.

This is a substantial limitation. The word `supported` in the output means “this status occurs in an admissible authored record.” It is not an independent researcher’s conclusion about the world. Adding genuine semantic verification would require a separate mechanism and its own evaluation.

## 3 The transition contract

An identical identifier and identical event content are treated as a duplicate. The same identifier with different content returns a conflict. A new event must belong to the current participant and branch. References to grounds must already exist. Changing a current claim requires an explicit predecessor that is still the head for that same subject and scope.

A simplified account of the procedure:

```text
check the identifier and duplicate
check the participant branch type and grounds
for a revision check the current predecessor
create a new state with the event added
return it without modifying the previous state
```

The implementation uses immutable objects and dictionaries protected against ordinary modification. Replaying a sequence operates on a candidate. If a subsequent event is unacceptable, the caller’s state is not partially changed. This is a guarantee of the single-process model, not proof of database resilience to a power outage.

## 4 One concrete run

The first two events are a constructed positive report `o1` and hypothesis `c1`. Next come a constructed negative control `o2` and revision `c2`, which refers to `c1`. The hypothesis text retains the same subject: “the cache preserves current metadata after an update.” Its status in this scope changes.

| Moment | Current claim | Status | Ground |
|---|---|---|---|
| Before the control | c1 | hypothesis | o1 |
| After the control | c2 | refuted | o2 |
| New review branch | c2 inherited from main | refuted | o2 from inherited history |

The previous `c1` remains in the history. The commitments `keep-uncertainty` and `retain-revisions` do not change. The new branch can see where the current claim was recorded. None of these facts establishes consciousness, lived experience, or LLM response quality. They test the declared relations in a finite data model.

## 5 Tests and a counterexample to the tool itself

The test suite covers redelivery, identifier collisions, missing grounds, a stale predecessor, an inadmissible scope change, branch isolation, an unknown result when history is absent, unchanged state after a failed batch, and preservation of status in two fixed response forms.

A separate test deliberately creates the claim “all numbers are even” and cites an existing cache-test record. The model accepts this structurally admissible record. That is precisely the behavior expected under its narrow contract. It shows that the existence of a reference does not prove a semantic connection. The distinction between a graph description and its validation conditions has an analogue in the separation of RDF data and SHACL shapes [7]; no such form by itself verifies every claim about the world.

Another example materializes the loss argument: two histories permit a test environment differently, but compression makes them identical. Enumerating the two possible Boolean answers shows that each is correct for only one of these histories. This demonstrates one concrete pair; the general argument appears in the part on continuity.

## 6 How to reproduce it

Python 3.11 or later is required. The example needs no additional libraries. Run these commands from the repository root:

```sh
python3 -m unittest discover -s examples -v
python3 examples/continuity.py
```

The first command tests the contract. The second prints JSON with initial and final states, fixed voice variants, and a loss witness. The input is open in `iris-events.json`; there is no hidden oracle. The output should not be described as the result of an AI experiment, because the model contains no AI component.

## 7 What the implementation does not establish

It has no author authentication, comprehensive historical trust scheme, concurrent writing, disk transactions, memory retrieval, profile-change mechanism, or evaluation of human interaction. A snapshot name supplied when branching is a caller’s label, not cryptographic evidence. Profile data is retained, but its influence on actual choice is not measured.

The fixed warm introduction in `render` demonstrates only the ability to change form while preserving the rest of a fixed text. It does not implement the depth of voice described in the book. Evaluating that requires varied situations and actual responses, with checks of attention, modality, disagreement, and human consequence.

This boundary defines the example’s value. It provides a small, concrete object for criticism: exactly what is tested, what passes, and what is missing. The durable implementation in the next part extends this core through concrete needs for recovery, concurrency, and decision freshness. The negative test of semantic support remains there too. Code volume does not measure ontological depth; reproducible distinctions between admissible and erroneous transitions make it testable.
