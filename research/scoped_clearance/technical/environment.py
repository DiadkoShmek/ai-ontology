"""Private finite document-workflow instrument, not a model-benefit study.

Each attempted controller step advances one action slot, including failures.
Updates occur before their declared slot, independently of proposed actions.
All updates end at target_step. The visible task states that cutoff; answers
before it receive an accounted before-target refusal. Thus later extra reads
cannot change the fixed comparison target. Only deliberate criterion updates
produce a visible task notice; source updates are discovered through tools.

The finite oracle checks declared exact answer/citation records at that target.
It is a separate host function, not semantic truth, and never enters a request.
Authored controls can establish instrument sensitivity, never model benefit.
"""

import copy
import hashlib
import json
import re
import time

import sandbox


ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,63}\Z")
DEFAULT_LIMITS = {"max_steps": 12, "max_cost": 40, "max_wall_seconds": 30,
                  "max_history_bytes": 65_536, "max_state_bytes": 16_384}
COSTS = {"controller": 1, "search": 1, "read": 2, "answer": 1, "abstain": 1, "failed": 1}


class InstrumentError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise InstrumentError(message)


def _keys(value, fields):
    return type(value) is dict and set(value) == set(fields)


def _text(value, maximum=8192):
    return type(value) is str and bool(value.strip()) and len(value) <= maximum


def _ident(value):
    return type(value) is str and ID.fullmatch(value) is not None


def _wire(value):
    # Validate through the existing step owner, then canonicalize JSON object
    # order. Host input dictionary order is not an experimental observation.
    checked = sandbox._json_bytes(value)
    return json.dumps(json.loads(checked), ensure_ascii=True, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode("ascii")


def _clone(value):
    return json.loads(_wire(value))


def _document(document):
    _require(_keys(document, ("document_id", "version", "scope", "title", "text")), "document fields")
    _require(_ident(document["document_id"]) and _ident(document["version"]), "document/version ID")
    _require(all(_text(document[key]) for key in ("scope", "title", "text")), "document text")


def _citation(citation):
    return (_keys(citation, ("document_id", "version", "scope", "quote")) and
            _ident(citation["document_id"]) and _ident(citation["version"]) and
            _text(citation["scope"]) and _text(citation["quote"]))


def _citation_key(citation):
    return tuple(citation[key] for key in ("document_id", "version", "scope", "quote"))


def _prepare(case, limits):
    """Validate/clone host data before any candidate invocation or grading."""
    _require(type(limits) is dict and set(limits) <= set(DEFAULT_LIMITS), "limit fields")
    settings = dict(DEFAULT_LIMITS, **_clone(limits))
    for key, low, high in (("max_steps", 1, 32), ("max_cost", 2, 256),
                           ("max_wall_seconds", 1, 120), ("max_history_bytes", 1, 131_072),
                           ("max_state_bytes", 1, 32_768)):
        _require(type(settings[key]) is int and low <= settings[key] <= high, "invalid limit:" + key)
    _require(len(_wire(case)) <= 262_144, "case byte limit")
    case = _clone(case)
    _require(_keys(case, ("task", "target_step", "documents", "updates", "oracle")), "case fields")
    _require(_text(case["task"]) and type(case["target_step"]) is int and
             1 <= case["target_step"] <= settings["max_steps"], "task/target step")
    _require(type(case["documents"]) is list and 1 <= len(case["documents"]) <= 32, "document count")
    documents, versions = {}, {}
    for document in case["documents"]:
        _document(document)
        ident = document["document_id"]
        _require(ident not in documents, "duplicate initial document")
        documents[ident] = copy.deepcopy(document)
        versions[(ident, document["version"])] = copy.deepcopy(document)
    _require(type(case["updates"]) is list and len(case["updates"]) <= 32, "update count")
    prior_step = 0
    final_documents = copy.deepcopy(documents)
    for update in case["updates"]:
        _require(type(update) is dict and update.get("kind") in ("document", "criterion"), "update kind")
        expected = ("at_step", "kind", "document") if update["kind"] == "document" else ("at_step", "kind", "task")
        _require(_keys(update, expected), "update fields")
        slot = update["at_step"]
        _require(type(slot) is int and prior_step <= slot <= case["target_step"] and slot >= 1, "update schedule")
        prior_step = slot
        if update["kind"] == "document":
            document = update["document"]
            _document(document)
            ident = document["document_id"]
            _require(ident in documents, "unknown update document")
            key = (ident, document["version"])
            _require(key not in versions, "immutable version overwritten")
            versions[key] = copy.deepcopy(document)
            final_documents[ident] = copy.deepcopy(document)
        else:
            _require(_text(update["task"]), "criterion task text")
    oracle = case["oracle"]
    _require(_keys(oracle, ("text", "citations")) and _text(oracle["text"]), "oracle fields/text")
    _require(type(oracle["citations"]) is list and 1 <= len(oracle["citations"]) <= 32 and
             all(_citation(citation) for citation in oracle["citations"]), "oracle citations")
    _require(len({_citation_key(c) for c in oracle["citations"]}) == len(oracle["citations"]), "duplicate oracle citation")
    for citation in oracle["citations"]:
        document = final_documents.get(citation["document_id"])
        _require(document is not None and document["version"] == citation["version"] and
                 document["scope"] == citation["scope"] and citation["quote"] in document["text"],
                 "oracle citation not supported at fixed target")
    return case, settings, documents


def _task(text, target_step):
    return (text + "\nAnswer target: the source/task state after action slot " + str(target_step) +
            ". Every controller attempt advances one slot. Source/task updates stop at that cutoff. "
            "An answer before the cutoff is refused; later reads do not move the target.")


def assess_answer(action, oracle):
    """Host-only finite equality check; never repairs submitted text/citations."""
    text_match = action["text"] == oracle["text"]
    citations_match = sorted(_citation_key(c) for c in action["citations"]) == sorted(
        _citation_key(c) for c in oracle["citations"])
    return {"evaluated": True, "text_match": text_match, "citations_match": citations_match,
            "useful": text_match and citations_match,
            "boundary": "Authored exact finite target; not a semantic entailment or natural-task judgment."}


def _proposal(value, max_state_bytes):
    if not _keys(value, ("action", "state")):
        return "proposal-fields"
    try:
        if len(_wire(value["state"])) > max_state_bytes:
            return "state-limit"
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return "state-invalid"
    action = value["action"]
    if type(action) is not dict or type(action.get("type")) is not str:
        return "action-fields"
    kind = action["type"]
    if kind == "search":
        valid = _keys(action, ("type", "query")) and _text(action["query"], 256)
    elif kind == "read":
        valid = (set(action) in ({"type", "document_id"}, {"type", "document_id", "version"}) and
                 _ident(action.get("document_id")) and ("version" not in action or _ident(action["version"])))
    elif kind == "answer":
        valid = (_keys(action, ("type", "text", "citations")) and _text(action["text"]) and
                 type(action["citations"]) is list and len(action["citations"]) <= 32 and
                 all(_citation(c) for c in action["citations"]))
        if valid:
            valid = len({_citation_key(c) for c in action["citations"]}) == len(action["citations"])
    elif kind == "abstain":
        valid = _keys(action, ("type", "reason")) and _text(action["reason"])
    else:
        return "unknown-action"
    return None if valid else "action-fields"


def run_episode(source, case, limits):
    """Return host transcript, visible receipts, accounting and a separate assessment.

    Only task/history/state/remaining_budget enter a controller request. Wall
    timings, capture diagnostics, host updates, case/oracle data and source are
    host-only. A budget admission refusal never executes the proposed tool.
    Instrument errors/record growth limits remain unscored, not false answers.
    """
    outcome = {"status": "instrument-error", "assessment": {"evaluated": False, "useful": False},
               "transcript": [], "history": [], "accounting": {
                   "steps": 0, "cost": 0, "native_wall_seconds": 0.0,
                   "host_wall_seconds": 0.0, "captured_output_utf8_bytes": 0}}
    try:
        case, settings, current = _prepare(case, limits)
    except (InstrumentError, ValueError, TypeError, UnicodeError, RecursionError) as exc:
        outcome["instrument_error"] = str(exc)[:160]
        return outcome
    outcome["limits"] = copy.deepcopy(settings)
    outcome["status"] = "running"
    outcome["rights"] = {"tools": ["search", "read", "answer", "abstain"], "costs": dict(COSTS),
                         "target_step": case["target_step"]}
    outcome["case_sha256"] = hashlib.sha256(_wire(case)).hexdigest()
    versions = {(doc["document_id"], doc["version"]): copy.deepcopy(doc) for doc in current.values()}
    state, task = None, case["task"]
    accounting, history = outcome["accounting"], outcome["history"]
    started = time.monotonic()
    for slot in range(1, settings["max_steps"] + 1):
        if accounting["cost"] + COSTS["controller"] + COSTS["failed"] > settings["max_cost"]:
            outcome["status"] = "cost-limit"
            break
        if time.monotonic() - started >= settings["max_wall_seconds"]:
            outcome["status"] = "wall-limit"
            break
        applied = []
        for update in case["updates"]:
            if update["at_step"] != slot:
                continue
            if update["kind"] == "document":
                document = copy.deepcopy(update["document"])
                current[document["document_id"]] = document
                versions[(document["document_id"], document["version"])] = document
            else:
                task = update["task"]
                history.append({"slot": slot, "kind": "task-notice", "task": task})
            applied.append(copy.deepcopy(update))
        request = {"task": _task(task, case["target_step"]), "history": copy.deepcopy(history),
                   "state": copy.deepcopy(state), "remaining_budget": {
                       "steps": settings["max_steps"] - accounting["steps"],
                       "cost": settings["max_cost"] - accounting["cost"]}}
        try:
            request_wire = _wire(request)
            if len(_wire(history)) > settings["max_history_bytes"] or len(request_wire) > sandbox.LIMITS["request_bytes"]:
                outcome["status"] = "instrument-limit"
                outcome["instrument_error"] = "visible request/history growth"
                break
            request = json.loads(request_wire)
        except (ValueError, TypeError, UnicodeError, RecursionError):
            outcome["status"] = "instrument-limit"
            outcome["instrument_error"] = "visible request serialization"
            break
        capture = sandbox.run_controller(source, request)
        accounting["steps"] += 1
        accounting["cost"] += COSTS["controller"]
        accounting["native_wall_seconds"] += capture["wall_seconds"]
        accounting["captured_output_utf8_bytes"] += len(capture["stdout"].encode("utf-8")) + len(capture["stderr"].encode("utf-8"))
        row = {"slot": slot, "request": request, "request_sha256": hashlib.sha256(request_wire).hexdigest(),
               "capture": capture, "host_updates": applied, "tool_cost": 0}
        outcome["transcript"].append(row)
        receipt = {"slot": slot, "kind": "action-receipt"}
        if capture["error"] is not None and capture["error"].startswith("confinement-unavailable:"):
            outcome["status"] = "instrument-error"
            outcome["instrument_error"] = capture["error"]
            break
        proposal = capture["terminal"]
        error = "controller-failed" if capture["error"] is not None else _proposal(proposal, settings["max_state_bytes"])
        action = None if error else proposal["action"]
        charge = COSTS["failed"] if error else COSTS[action["type"]]
        if time.monotonic() - started > settings["max_wall_seconds"]:
            receipt.update(ok=False, error="wall-budget-refused")
            charge = COSTS["failed"]
            outcome["status"] = "wall-limit"
        elif accounting["cost"] + charge > settings["max_cost"]:
            receipt.update(ok=False, error="cost-budget-refused")
            charge = COSTS["failed"]
            outcome["status"] = "cost-limit"
        elif error:
            receipt.update(ok=False, error=error)
        else:
            state = copy.deepcopy(proposal["state"])
            kind = action["type"]
            receipt["action"] = copy.deepcopy(action)
            if kind == "search":
                terms = action["query"].casefold().split()
                matches = [doc for doc in current.values() if all(term in (doc["title"] + " " + doc["text"]).casefold() for term in terms)]
                receipt.update(ok=True, result=[{key: doc[key] for key in ("document_id", "version", "scope", "title")}
                                               for doc in sorted(matches, key=lambda item: item["document_id"])])
            elif kind == "read":
                document = (versions.get((action["document_id"], action["version"])) if "version" in action
                            else current.get(action["document_id"]))
                if document is None:
                    receipt.update(ok=False, error="not-found")
                else:
                    receipt.update(ok=True, result=copy.deepcopy(document))
            elif kind == "answer":
                if slot < case["target_step"]:
                    receipt.update(ok=False, error="before-target")
                else:
                    receipt.update(ok=True, result="answer-recorded")
                    outcome["status"] = "answered"
                    outcome["assessment"] = assess_answer(action, case["oracle"])
            else:
                receipt.update(ok=True, result="abstention-recorded")
                outcome["status"] = "abstained"
                outcome["assessment"] = {"evaluated": True, "useful": False, "reason": action["reason"]}
        accounting["cost"] += charge
        row["tool_cost"] = charge
        row["receipt"] = copy.deepcopy(receipt)
        history.append(receipt)
        if outcome["status"] in ("answered", "abstained", "wall-limit", "cost-limit"):
            break
    else:
        outcome["status"] = "step-limit"
    accounting["host_wall_seconds"] = time.monotonic() - started
    outcome["boundary"] = ("Private authored finite instrument. Tool receipts are local observations; "
                           "no external action, model benefit, privacy respect or method rebuilding is certified. "
                           "Output cost counts captured strings re-encoded as UTF-8; invalid-wire replacement "
                           "may overcount native bytes. Timings and oracle never enter requests.")
    return outcome
