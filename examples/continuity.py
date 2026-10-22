"""A finite in-memory projection model, not an AI agent or identity detector.

No network, tools, persistence, semantic entailment, authentication or LLM calls.
Events are authored fixture data. Replay is ordered and transactional per call.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


class Conflict(ValueError):
    """The supplied finite event history violates this model's contract."""


@dataclass(frozen=True)
class Event:
    id: str
    actor: str
    branch: str
    kind: str
    topic: str
    status: str
    text: str
    scope: str
    basis: tuple[str, ...] = ()
    revises: str | None = None
    origin: str = "fixture"


@dataclass(frozen=True)
class State:
    actor: str
    branch: str
    profile: str
    commitments: tuple[str, ...]
    events: Mapping[str, Event]
    current: Mapping[tuple[str, str], str]
    parent: str | None = None
    retired: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))


def empty(actor: str = "iris", branch: str = "main") -> State:
    return State(actor, branch, "iris/1", ("keep-uncertainty", "retain-revisions"),
                 MappingProxyType({}), MappingProxyType({}))


def apply(state: State, event: Event) -> State:
    if not isinstance(event, Event) or not isinstance(event.id, str):
        raise Conflict("invalid-event")
    # Exact repeats are idempotent, including inherited events after a fork.
    if event.id in state.events:
        if state.events[event.id] == event:
            return state
        raise Conflict("event-id-collision")
    if any(not isinstance(x, str) or not x.strip() for x in (
        event.id, event.actor, event.branch, event.kind, event.topic,
        event.status, event.text, event.scope, event.origin,
    )):
        raise Conflict("empty-or-invalid-field")
    if event.actor != state.actor or event.branch != state.branch:
        raise Conflict("wrong-actor-or-branch")
    if event.kind not in {"observation", "claim"}:
        raise Conflict("unknown-kind")
    if (not isinstance(event.basis, tuple)
            or any(not isinstance(x, str) or not x.strip() for x in event.basis)
            or len(set(event.basis)) != len(event.basis)
            or (event.revises is not None and not isinstance(event.revises, str))):
        raise Conflict("invalid-basis")
    if any(x not in state.events for x in event.basis):
        raise Conflict("missing-basis")
    current = dict(state.current)
    key = (event.topic, event.scope)
    if event.kind == "observation":
        if event.status != "recorded" or event.revises is not None or event.basis:
            raise Conflict("invalid-observation")
    else:
        if event.status not in {"hypothesis", "supported", "refuted", "unknown"}:
            raise Conflict("unknown-claim-status")
        if event.status != "unknown" and not event.basis:
            raise Conflict("unsupported-status")
        if event.revises is None:
            if key in current:
                raise Conflict("explicit-revision-required")
        else:
            previous = state.events.get(event.revises)
            if previous is None or previous.kind != "claim":
                raise Conflict("missing-claim-predecessor")
            if (previous.topic, previous.scope) != key:
                raise Conflict("revision-changed-subject")
            if current.get(key) != event.revises:
                raise Conflict("stale-predecessor")
        current[key] = event.id
    events = dict(state.events)
    events[event.id] = event
    return replace(state, events=MappingProxyType(events), current=MappingProxyType(current))


def replay(state: State, events: tuple[Event, ...]) -> State:
    # State is immutable: an exception cannot partially mutate the caller.
    candidate = state
    for event in events:
        candidate = apply(candidate, event)
    return candidate


def fork(state: State, branch: str, snapshot_id: str) -> State:
    if not branch.strip() or branch == state.branch or not snapshot_id.strip():
        raise Conflict("invalid-fork")
    # Shared values are immutable. Future dictionaries are replaced on apply.
    # snapshot_id is a caller label, NOT a cryptographic/authenticity claim.
    return replace(state, branch=branch, parent=snapshot_id)


def knowledge(state: State, topic: str, scope: str) -> dict:
    key = (topic, scope)
    if key not in state.current:
        return {"status": "unknown", "reason": "no-accessible-claim"}
    event = state.events[state.current[key]]
    return {"status": event.status, "claim": event.id, "text": event.text,
            "scope": event.scope, "basis": list(event.basis),
            "recorded_in_branch": event.branch, "current_branch": state.branch}


def render(view: dict, voice: str) -> str:
    # Deliberately fixed rendering. This cannot establish quality of LLM voice.
    if voice not in {"brief", "warm"}:
        raise Conflict("unknown-voice")
    lead = {"hypothesis": "Гіпотеза", "supported": "Підтримано в цій області",
            "refuted": "Спростовано в цій області", "unknown": "Невідомо"}[view["status"]]
    content = f'{lead}: {view.get("text", "немає доступного твердження")}.'
    return content if voice == "brief" else f'Розберімося разом. {content}'


def read_fixture() -> tuple[Event, ...]:
    raw = json.loads(Path(__file__).with_name("iris-events.json").read_text(encoding="utf-8"))
    return tuple(Event(**{**e, "basis": tuple(e.get("basis", []))}) for e in raw)


def demonstration() -> dict:
    events = read_fixture()
    before = replay(empty(), events[:2])
    after = replay(before, events[2:])
    branch = fork(after, "review", "authored-snapshot-1")
    view = knowledge(branch, "cache-current", "updates-A")
    left = {"staging": True, "production": False}
    right = {"staging": False, "production": True}
    compress = lambda history: "one environment awaits a test"
    return {
        "kind": "constructed-deterministic-demonstration",
        "llm_trials": 0,
        "before": knowledge(before, "cache-current", "updates-A"),
        "after": view,
        "history_retained": len(after.events) == 4,
        "commitments_retained": before.commitments == after.commitments,
        "brief": render(view, "brief"), "warm": render(view, "warm"),
        "loss_witness": {"same_summary": compress(left) == compress(right),
                         "different_staging_answers": left["staging"] != right["staging"]},
        "limits": ["authored evidence not semantically verified", "no persistence or concurrency",
                   "no identity or consciousness measurement", "no authentication"],
    }


if __name__ == "__main__":
    print(json.dumps(demonstration(), ensure_ascii=False, indent=2))
