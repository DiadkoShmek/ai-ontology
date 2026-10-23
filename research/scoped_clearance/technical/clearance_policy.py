"""Private finite clearance contract: authored fixtures, not model results.

The principal old rule blocks every quote/derive route to private material.
The new rule cuts a route at a valid cleared output, including a private
output itself. All other private routes still block. Clearances are stipulated
fixture authority, not cryptographically authenticated grants. Current policy
is known in M1; these functions do not claim autonomous rule discovery.
"""

import copy
import hashlib
import json
import random
import re

import release_workflow as base

MAX_BYTES = 8192
TOKEN_KEYS = {"id", "node", "version", "digest", "project", "recipient", "purpose", "epoch"}
WRAPPER_KEYS = {"manifest", "recipient", "purpose", "versions", "clearances", "revoked",
                "epoch_revoked", "delivery_purposes"}
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _require(condition, reason):
    if not condition:
        raise base.InvalidInstrument(reason)


def value_digest(value):
    """Digest exact UTF-8 value, not its JSON encoding or a whole node."""
    return hashlib.sha256(value.encode("utf-8", "strict")).hexdigest()


def validate_wrapper(wrapper):
    """Validate exact bounded ASCII wire; mismatched/revoked grants stay inert data."""
    try:
        raw = base.canonical(wrapper)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise base.InvalidInstrument("clearance wrapper JSON") from exc
    _require(len(raw) <= MAX_BYTES, "clearance wrapper exceeds read cap")
    wrapper = json.loads(raw)
    _require(type(wrapper) is dict and set(wrapper) == WRAPPER_KEYS, "clearance wrapper fields")
    try:
        manifest = base.validate_manifest(wrapper["manifest"])
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise base.InvalidInstrument("clearance manifest: " + str(exc)[:120]) from exc
    _require(base._id(wrapper["recipient"]) and base._id(wrapper["purpose"]), "clearance target scope")
    nodes = {n["id"]: n for n in manifest["nodes"]}
    versions = wrapper["versions"]
    _require(type(versions) is dict and set(versions) == set(nodes) and
             all(base._id(v) for v in versions.values()), "current version bindings")
    grants = wrapper["clearances"]
    _require(type(grants) is list and len(grants) <= 64, "clearance count")
    seen = set()
    for grant in grants:
        _require(type(grant) is dict and set(grant) == TOKEN_KEYS, "clearance fields")
        _require(all(base._id(grant[k]) for k in TOKEN_KEYS - {"digest"}) and
                 type(grant["digest"]) is str and HEX.fullmatch(grant["digest"]) is not None,
                 "clearance values")
        _require(grant["id"] not in seen, "duplicate clearance ID")
        seen.add(grant["id"])
    revoked = wrapper["revoked"]
    _require(type(revoked) is list and len(revoked) <= 64 and all(base._id(x) for x in revoked) and
             revoked == sorted(set(revoked)), "revoked token IDs")
    _require(type(wrapper["epoch_revoked"]) is bool, "epoch revocation flag")
    purposes = wrapper["delivery_purposes"]
    _require(type(purposes) is dict and set(purposes) == {d["delivery_id"] for d in manifest["deliveries"]} and
             all(base._id(p) for p in purposes.values()), "delivery purpose bindings")
    return copy.deepcopy(wrapper)


def _matrix_cuts(wrapper):
    """Gold grant matching uses equality of the complete scoped material tuple."""
    if wrapper["epoch_revoked"]:
        return set()
    m = wrapper["manifest"]
    nodes = {n["id"]: n for n in m["nodes"]}
    expected = {(n, wrapper["versions"][n], value_digest(nodes[n]["value"]), m["project"],
                 wrapper["recipient"], wrapper["purpose"], m["epoch"]) for n in nodes}
    return {g["node"] for g in wrapper["clearances"] if g["id"] not in wrapper["revoked"] and
            (g["node"], g["version"], g["digest"], g["project"], g["recipient"], g["purpose"], g["epoch"]) in expected}


def oracle_forbidden(wrapper, *, old=False):
    """Independent finite gold: remove cleared outgoing paths, then matrix closure."""
    w = validate_wrapper(wrapper)
    _require(type(old) is bool, "old-policy flag")
    m = w["manifest"]
    cuts = set() if old else _matrix_cuts(w)
    ids = sorted(n["id"] for n in m["nodes"])
    index = {n: i for i, n in enumerate(ids)}
    reach = [[False] * len(ids) for _ in ids]
    for edge in m["edges"]:
        if edge["type"] in ("quote", "derive") and edge["source"] not in cuts:
            reach[index[edge["source"]]][index[edge["target"]]] = True
    for middle in range(len(ids)):
        for source in range(len(ids)):
            if reach[source][middle]:
                for target in range(len(ids)):
                    reach[source][target] = reach[source][target] or reach[middle][target]
    private = [index[n["id"]] for n in m["nodes"] if n["visibility"] == "private" and n["id"] not in cuts]
    return {n for n in ids if n not in cuts and
            (index[n] in private or any(reach[index[n]][p] for p in private))}


def generic_forbidden(wrapper, *, old=False):
    """Fixed stronger generic comparator: per-root graph walk, never calls gold."""
    w = validate_wrapper(wrapper)
    _require(type(old) is bool, "old-policy flag")
    m = w["manifest"]
    nodes = {n["id"]: n for n in m["nodes"]}
    cut = set()
    if not old and not w["epoch_revoked"]:
        for grant in w["clearances"]:
            node = nodes.get(grant["node"])
            if node is None or grant["id"] in w["revoked"]:
                continue
            if grant["project"] != m["project"] or grant["epoch"] != m["epoch"]:
                continue
            if grant["recipient"] != w["recipient"] or grant["purpose"] != w["purpose"]:
                continue
            if grant["version"] != w["versions"][node["id"]]:
                continue
            if hashlib.sha256(node["value"].encode("utf-8")).hexdigest() != grant["digest"]:
                continue
            cut.add(node["id"])
    outgoing = {n: [] for n in nodes}
    for edge in m["edges"]:
        if edge["type"] != "inspiration":
            outgoing[edge["source"]].append(edge["target"])
    blocked = set()
    for root in nodes:
        pending, visited = [root], set()
        while pending:
            node = pending.pop()
            if node in visited or node in cut:
                continue
            visited.add(node)
            if nodes[node]["visibility"] == "private":
                blocked.add(root)
                break
            pending.extend(outgoing[node])
    return blocked


def _plan_from_blocked(w, blocked):
    """Same snapshot, exact delivery scope, no reconstruction of a past corpus."""
    m = w["manifest"]
    withdraw, notify, unresolved = set(), set(), set()
    for d in m["deliveries"]:
        if (d["status"] != "delivered" or d["project"] != m["project"] or d["epoch"] != m["epoch"] or
                d["recipient"] != w["recipient"] or w["delivery_purposes"][d["delivery_id"]] != w["purpose"]):
            continue
        if d["field"] not in blocked:
            continue
        withdraw.add(d["delivery_id"])
        if m["consent"].get(d["recipient"], False):
            notify.add(d["recipient"])
        else:
            unresolved.add(d["delivery_id"])
    return {"release": sorted(set(m["requested"]) - blocked), "withdraw": sorted(withdraw),
            "notify": sorted(notify), "unresolved": sorted(unresolved)}


def expected_plan(wrapper, *, old=False, current_contract=None):
    """Known new contract by default; current_contract=False selects the old rule."""
    _require(type(old) is bool and (current_contract is None or type(current_contract) is bool), "policy selector")
    _require(not (old and current_contract is True), "conflicting policy selectors")
    old = old if current_contract is None else not current_contract
    w = validate_wrapper(wrapper)
    return _plan_from_blocked(w, oracle_forbidden(w, old=old))


def baseline_plan(wrapper, *, old=False):
    """Authored generic control is deliberately sufficient; not a generated M1."""
    w = validate_wrapper(wrapper)
    return _plan_from_blocked(w, generic_forbidden(w, old=old))


def grade_plan(wrapper, plan, *, old=False):
    """Grade a canonical proposed plan only; does not execute or attest effects."""
    actual = base.parse_plan(plan)
    expected = expected_plan(wrapper, old=old)
    return {"correct": actual == expected, "expected": expected,
            "missing": {k: sorted(set(expected[k]) - set(actual[k])) for k in expected},
            "extra": {k: sorted(set(actual[k]) - set(expected[k])) for k in expected},
            "boundary": "Finite stipulated current contract and immutable synthetic snapshot; plan, not artifact grading."}


def make_witness(prefix="c", *, clear_second=True, consent=True, cycle=False, depth=2):
    """Two content parents: clearing one cannot erase another private route."""
    _require(base._id(prefix) and all(type(x) is bool for x in (clear_second, consent, cycle)) and
             type(depth) is int and 2 <= depth <= 6, "witness parameters")
    names = {k: prefix + ":" + k for k in ("field", "left", "right", "secret", "public", "inspired")}
    m = {"project": prefix + ":project", "epoch": prefix + ":epoch", "nodes": [
        {"id": n, "visibility": "private" if k == "secret" else "public", "value": "synthetic-" + k}
        for k, n in names.items()], "edges": [
            {"source": names["field"], "type": "derive", "target": names["left"]},
            {"source": names["field"], "type": "quote", "target": names["right"]},
            {"source": names["left"], "type": "derive", "target": names["secret"]},
            {"source": names["right"], "type": "quote", "target": names["secret"]},
            {"source": names["inspired"], "type": "inspiration", "target": names["secret"]}],
         "requested": sorted(names[k] for k in ("field", "public", "inspired")), "deliveries": [],
         "consent": {prefix + ":recipient": consent}}
    if depth > 2:
        m["edges"] = [e for e in m["edges"] if e["source"] not in (names["left"], names["right"])]
        for branch in ("left", "right"):
            chain = [names[branch]]
            for level in range(depth - 2):
                ident = prefix + ":" + branch + "-m" + str(level)
                m["nodes"].append({"id": ident, "visibility": "public", "value": "intermediate-" + str(level)})
                chain.append(ident)
            chain.append(names["secret"])
            m["edges"].extend({"source": a, "type": "derive", "target": b} for a, b in zip(chain, chain[1:]))
    if cycle:
        m["edges"].append({"source": names["right"], "type": "derive", "target": names["field"]})
    w = {"manifest": m, "recipient": prefix + ":recipient", "purpose": prefix + ":purpose",
         "versions": {n["id"]: prefix + ":v1" for n in m["nodes"]}, "clearances": [], "revoked": [],
         "epoch_revoked": False, "delivery_purposes": {}}
    for k in ("left", "right"):
        node = next(n for n in m["nodes"] if n["id"] == names[k])
        w["clearances"].append({"id": prefix + ":token-" + k, "node": names[k],
                               "version": w["versions"][names[k]], "digest": value_digest(node["value"]),
                               "project": m["project"], "recipient": w["recipient"] if k == "left" or clear_second else prefix + ":other",
                               "purpose": w["purpose"], "epoch": m["epoch"]})
    return validate_wrapper(w), names


def paired_worlds(prefix="pair"):
    """Payloads differ ONLY in a clearance recipient, never in ordinary graph."""
    yes, _ = make_witness(prefix)
    no = copy.deepcopy(yes)
    no["clearances"][1]["recipient"] = prefix + ":other"
    return yes, validate_wrapper(no)


def _renamed(wrapper, seed):
    """Opaque IDs and independently shuffled ordered arrays, no outcome labels."""
    w = copy.deepcopy(wrapper)
    rng = random.Random(seed)
    m = w["manifest"]
    values = {m["project"], m["epoch"], w["recipient"], w["purpose"]}
    values.update(w["versions"].values())
    values.update(n["id"] for n in m["nodes"])
    values.update(m["consent"])
    values.update(w["revoked"])
    values.update(w["delivery_purposes"].values())
    for g in w["clearances"]:
        values.update(g[k] for k in TOKEN_KEYS - {"digest"})
    for d in m["deliveries"]:
        values.update(d[k] for k in ("delivery_id", "recipient", "field", "project", "epoch"))
    shuffled = sorted(values)
    rng.shuffle(shuffled)
    lookup = {old: "n" + str(seed) + "x" + str(i) for i, old in enumerate(shuffled)}
    def rename(x):
        if type(x) is str:
            return lookup.get(x, x)
        if type(x) is list:
            return [rename(y) for y in x]
        if type(x) is dict:
            return {lookup.get(k, k): rename(v) for k, v in x.items()}
        return x
    w = rename(w)
    for key in ("nodes", "edges", "deliveries"):
        rng.shuffle(w["manifest"][key])
    rng.shuffle(w["clearances"])
    w["manifest"]["requested"].sort()
    w["revoked"].sort()
    return validate_wrapper(w)


def transfer_cases(seed=811):
    """Authored finite transfers, independent instances not independent domains."""
    _require(type(seed) is int and 0 <= seed <= 1_000_000, "transfer seed")
    w, names = make_witness("t")
    worlds = [w, paired_worlds("t")[1]]
    for field in ("project", "recipient", "purpose", "epoch", "version", "digest"):
        x = copy.deepcopy(w)
        x["clearances"][1][field] = "0" * 64 if field == "digest" else "foreign"
        worlds.append(x)
    x = copy.deepcopy(w);x["revoked"] = [x["clearances"][1]["id"]];worlds.append(x)
    x = copy.deepcopy(w);x["epoch_revoked"] = True;worlds.append(x)
    worlds.append(make_witness("t", cycle=True)[0])
    x = copy.deepcopy(w)
    # An alternate uncleared private parent survives both valid parent cuts.
    x["manifest"]["edges"].append({"source": names["field"], "type": "quote", "target": names["secret"]})
    worlds.append(x)
    for consent in (True, False):
        x = copy.deepcopy(paired_worlds("t")[1])
        m = x["manifest"];m["consent"][x["recipient"]] = consent
        for i, change in enumerate(({}, {"status": "queued"}, {"project": "foreign"},
                                    {"epoch": "foreign"}, {"recipient": "foreign"}, {})):
            row = {"delivery_id": "d" + str(i), "recipient": x["recipient"], "field": names["field"],
                   "status": "delivered", "project": m["project"], "epoch": m["epoch"], **change}
            m["deliveries"].append(row)
            x["delivery_purposes"][row["delivery_id"]] = "foreign" if i == 5 else x["purpose"]
        worlds.append(x)
    # Structural, not merely lexical, transfer: longer routes with a cycle.
    worlds.append(make_witness("deep", depth=5)[0])
    worlds.append(make_witness("deepcycle", clear_second=False, depth=4, cycle=True)[0])
    # A different private ancestor remains blocking even when the first is covered.
    x, nx = make_witness("multi")
    second = {"id": "multi:second-private", "visibility": "private", "value": "second-source"}
    x["manifest"]["nodes"].append(second)
    x["versions"][second["id"]] = "multi:v2"
    x["manifest"]["edges"].append({"source": nx["field"], "type": "quote", "target": second["id"]})
    worlds.append(x)
    # A valid clearance may cover a private output itself, including zero-length routes.
    x, nx = make_witness("direct")
    secret = next(n for n in x["manifest"]["nodes"] if n["id"] == nx["secret"])
    grant = copy.deepcopy(x["clearances"][0])
    grant.update(id="direct:token-secret", node=secret["id"], version=x["versions"][secret["id"]],
                 digest=value_digest(secret["value"]))
    x["clearances"] = [grant]
    x["manifest"]["requested"] = sorted(x["manifest"]["requested"] + [secret["id"]])
    worlds.append(x)
    # Changed material is its own binding: matching recomputed hashes versus stale grants.
    x, _ = make_witness("material", depth=3)
    for i, node in enumerate(x["manifest"]["nodes"]):
        node["value"] = "payload-" + hashlib.sha256((str(seed) + ":" + str(i)).encode()).hexdigest()[:20]
    stale = copy.deepcopy(x)
    values = {n["id"]: n["value"] for n in x["manifest"]["nodes"]}
    for grant in x["clearances"]:
        grant["digest"] = value_digest(values[grant["node"]])
    worlds.extend((x, stale))
    return [_renamed(validate_wrapper(x), seed + i) for i, x in enumerate(worlds)]
