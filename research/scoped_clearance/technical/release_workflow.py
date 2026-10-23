"""Private three-criterion release calibration, not a model-rebuilding study.

Manifest values are authored synthetic data. Executor has no criterion input
and never consults either policy implementation. SQLite effects are local only.
Oracle uses a reachability matrix; calibration baselines use a separate walker.
Generic parametric closure can suffice once two labels identify the criterion.
"""

import copy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3


CRITERIA = ("direct", "content-path", "all-links")
EDGE_TYPES = {"quote", "derive", "inspiration"}
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,63}\Z")


class InvalidInstrument(ValueError):
    pass


class InvalidPlan(ValueError):
    pass


def _require(test, reason):
    if not test:
        raise InvalidInstrument(reason)


def _id(value):
    return type(value) is str and ID.fullmatch(value) is not None


def _keys(value, names):
    return type(value) is dict and set(value) == set(names)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("ascii")


def validate_manifest(manifest):
    _require(_keys(manifest, ("project", "epoch", "nodes", "edges", "requested", "deliveries", "consent")), "manifest fields")
    _require(_id(manifest["project"]) and _id(manifest["epoch"]), "manifest scope")
    _require(type(manifest["nodes"]) is list and 1 <= len(manifest["nodes"]) <= 64, "node count")
    nodes = {}
    for node in manifest["nodes"]:
        _require(_keys(node, ("id", "visibility", "value")) and _id(node["id"]), "node fields")
        _require(node["id"] not in nodes and node["visibility"] in ("public", "private"), "node identity/label")
        _require(type(node["value"]) is str and len(node["value"]) <= 4096, "node value")
        try:
            node["value"].encode("utf-8", "strict")
        except UnicodeError as exc:
            raise InvalidInstrument("node value Unicode") from exc
        nodes[node["id"]] = node
    _require(type(manifest["edges"]) is list and len(manifest["edges"]) <= 256, "edge count")
    seen = set()
    for edge in manifest["edges"]:
        _require(_keys(edge, ("source", "type", "target")), "edge fields")
        _require(type(edge["source"]) is str and type(edge["target"]) is str and
                 edge["source"] in nodes and edge["target"] in nodes and
                 type(edge["type"]) is str and edge["type"] in EDGE_TYPES, "edge values")
        triple = (edge["source"], edge["type"], edge["target"])
        _require(triple not in seen, "duplicate edge")
        seen.add(triple)
    requested = manifest["requested"]
    _require(type(requested) is list and 1 <= len(requested) <= 32 and
             all(type(field) is str and field in nodes for field in requested) and
             requested == sorted(set(requested)), "requested fields")
    _require(type(manifest["deliveries"]) is list and len(manifest["deliveries"]) <= 64, "delivery count")
    delivered_ids = set()
    for row in manifest["deliveries"]:
        _require(_keys(row, ("delivery_id", "recipient", "field", "status", "project", "epoch")) and
                 all(_id(row[key]) for key in ("delivery_id", "recipient", "project", "epoch")), "delivery fields")
        _require(row["delivery_id"] not in delivered_ids and type(row["field"]) is str and row["field"] in nodes and
                 row["status"] in ("queued", "delivered"), "delivery values")
        delivered_ids.add(row["delivery_id"])
    _require(type(manifest["consent"]) is dict and len(manifest["consent"]) <= 32 and
             all(_id(recipient) and type(allowed) is bool for recipient, allowed in manifest["consent"].items()), "recipient consent")
    try:
        raw = canonical(manifest)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise InvalidInstrument("manifest JSON") from exc
    _require(len(raw) <= 8192, "manifest exceeds existing read document text cap")
    return copy.deepcopy(manifest)


def parse_plan(value):
    """Lists must already be sorted unique IDs; no silent plan repair."""
    def unique(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise InvalidPlan("duplicate plan key")
            result[key] = item
        return result
    if type(value) is str:
        if len(value) > 8192:
            raise InvalidPlan("plan text cap")
        try:
            value = json.loads(value, object_pairs_hook=unique)
        except (ValueError, RecursionError) as exc:
            raise InvalidPlan("plan JSON") from exc
    if not _keys(value, ("release", "withdraw", "notify", "unresolved")):
        raise InvalidPlan("plan fields")
    for key, values in value.items():
        if not (type(values) is list and len(values) <= 64 and all(_id(item) for item in values)
                and values == sorted(set(values))):
            raise InvalidPlan("noncanonical plan list:" + key)
    return copy.deepcopy(value)


def _matrix_forbidden(manifest, criterion):
    """Independent oracle: boolean adjacency matrix and Floyd-Warshall closure."""
    _require(criterion in CRITERIA, "unknown criterion")
    ids = sorted(node["id"] for node in manifest["nodes"])
    index = {ident: position for position, ident in enumerate(ids)}
    size = len(ids)
    matrix = [[False] * size for _ in ids]
    for edge in manifest["edges"]:
        if criterion == "all-links" or edge["type"] in ("quote", "derive"):
            matrix[index[edge["source"]]][index[edge["target"]]] = True
    if criterion != "direct":
        for middle in range(size):
            for source in range(size):
                if matrix[source][middle]:
                    for target in range(size):
                        matrix[source][target] |= matrix[middle][target]
    private = {index[node["id"]] for node in manifest["nodes"] if node["visibility"] == "private"}
    return {ident for ident in ids if index[ident] in private or any(matrix[index[ident]][target] for target in private)}


def _walk_forbidden(manifest, criterion):
    """Authored simpler control; deliberately does not call the matrix oracle."""
    _require(criterion in CRITERIA, "unknown baseline criterion")
    private = {node["id"] for node in manifest["nodes"] if node["visibility"] == "private"}
    outgoing = {}
    for edge in manifest["edges"]:
        if criterion == "all-links" or edge["type"] in ("quote", "derive"):
            outgoing.setdefault(edge["source"], []).append(edge["target"])
    blocked = set(private)
    for node in manifest["nodes"]:
        pending = [(target, 1) for target in outgoing.get(node["id"], [])]
        seen = set()
        while pending:
            target, depth = pending.pop()
            if target in private:
                blocked.add(node["id"])
                break
            if target in seen or criterion == "direct":
                continue
            seen.add(target)
            pending.extend((child, depth + 1) for child in outgoing.get(target, []))
    return blocked


def make_witness(prefix="w", depth=2, cycle=False):
    """Minimum four contrast fields plus optional deeper/cyclic raw dependencies."""
    _require(_id(prefix) and type(depth) is int and 2 <= depth <= 8 and type(cycle) is bool, "witness parameters")
    names = {key: prefix + ":" + key for key in ("public", "direct", "deep", "inspiration", "private")}
    middle = [prefix + ":mid" + str(index) for index in range(depth - 1)]
    nodes = [{"id": ident, "visibility": "private" if key == "private" else "public", "value": "synthetic-" + key}
             for key, ident in names.items()]
    nodes += [{"id": ident, "visibility": "public", "value": "synthetic-intermediate"} for ident in middle]
    edges = [{"source": names["direct"], "type": "quote", "target": names["private"]},
             {"source": names["inspiration"], "type": "inspiration", "target": names["private"]}]
    chain = [names["deep"]] + middle + [names["private"]]
    edges += [{"source": first, "type": "derive", "target": second} for first, second in zip(chain, chain[1:])]
    if cycle:
        edges.append({"source": middle[-1], "type": "quote", "target": middle[0]})
    manifest = {"project": prefix + ":project", "epoch": prefix + ":epoch", "nodes": nodes, "edges": edges,
                "requested": sorted(names[key] for key in ("public", "direct", "deep", "inspiration")),
                "deliveries": [], "consent": {}}
    return validate_manifest(manifest), names


def identifiability_witness(manifest, probe_fields):
    manifest = validate_manifest(manifest)
    _require(len(probe_fields) == 2 and all(field in manifest["requested"] for field in probe_fields), "probe fields")
    signatures, allowed = {}, {}
    for criterion in CRITERIA:
        forbidden = _matrix_forbidden(manifest, criterion)
        signatures[criterion] = ["object" if field in forbidden else "accept" for field in probe_fields]
        allowed[criterion] = sorted(set(manifest["requested"]) - forbidden)
    return {"owner_label_signatures": signatures, "allowed_sets": allowed,
            "labels_identify_all_three": len({tuple(values) for values in signatures.values()}) == 3,
            "blind_optimum_exists": len({tuple(values) for values in allowed.values()}) == 1,
            "boundary": "Finite declared family: selecting one generic closure parameter can suffice; not new algorithm evidence."}


def _scoped_delivered(manifest):
    return [row for row in manifest["deliveries"] if row["status"] == "delivered" and
            row["project"] == manifest["project"] and row["epoch"] == manifest["epoch"]]


def baseline_plan(manifest, policy, blocked_ids=()):
    """Authored calibration only; fixed parametric code can solve the family."""
    manifest = validate_manifest(manifest)
    if policy in CRITERIA:
        blocked = _walk_forbidden(manifest, policy)
        release_blocked, repair_blocked, ambiguous = blocked, blocked, set()
    elif policy == "unknown":
        sets = [_walk_forbidden(manifest, criterion) for criterion in CRITERIA]
        release_blocked = set.union(*sets)
        repair_blocked = set.intersection(*sets)
        ambiguous = release_blocked - repair_blocked
    elif policy == "withhold":
        release_blocked = repair_blocked = {node["id"] for node in manifest["nodes"]}
        ambiguous = set()
    elif policy == "point":
        _require(all(_id(ident) for ident in blocked_ids), "point-control IDs")
        release_blocked = repair_blocked = set(blocked_ids)
        ambiguous = set()
    else:
        raise InvalidInstrument("unknown authored baseline")
    withdraw, notify, unresolved = set(), set(), set()
    for row in _scoped_delivered(manifest):
        if row["field"] in repair_blocked:
            withdraw.add(row["delivery_id"])
            if manifest["consent"].get(row["recipient"], False):
                notify.add(row["recipient"])
            else:
                unresolved.add(row["delivery_id"])
        elif row["field"] in ambiguous:
            unresolved.add(row["delivery_id"])
    return {"release": sorted(set(manifest["requested"]) - release_blocked), "withdraw": sorted(withdraw),
            "notify": sorted(notify), "unresolved": sorted(unresolved)}


def read_artifact(path):
    """Reopen actual SQLite bytes read-only; do not grade a proposed plan."""
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        def rows(table, order):
            return [dict(row) for row in connection.execute("SELECT * FROM " + table + " ORDER BY " + order)]
        return {"released": rows("released", "field"), "remaining": rows("deliveries", "delivery_id"),
                "history": rows("delivery_history", "delivery_id"),
                "withdrawals": rows("withdrawal_receipts", "delivery_id"),
                "notices": rows("notice_receipts", "recipient"), "unresolved": rows("unresolved", "delivery_id"),
                "metadata": dict(connection.execute("SELECT key,value FROM metadata"))}


def _bound_artifact(path, manifest):
    """A host source/artifact mismatch is an instrument error, never a score."""
    try:
        artifact = read_artifact(path)
    except sqlite3.Error as exc:
        raise InvalidInstrument("unreadable effect artifact") from exc
    _require(artifact["metadata"] == {"manifest_sha256": hashlib.sha256(canonical(manifest)).hexdigest()},
             "effect artifact manifest mismatch")
    return artifact


def execute_plan(path, manifest, plan):
    """Criterion-free mechanical local effects. Existing paths are never reset.

    Path is supplied by the trusted caller, not by a plan or manifest. IDs enter
    SQL only as bound values. All releases—including unsafe ones—are retained.
    Withdrawal affects current delivery rows, not immutable delivery history.
    """
    manifest, plan = validate_manifest(manifest), parse_plan(plan)
    requested = set(manifest["requested"])
    if not set(plan["release"]) <= requested:
        raise InvalidPlan("release outside requested fields")
    path = Path(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(descriptor)
    node_values = {node["id"]: node["value"] for node in manifest["nodes"]}
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO metadata VALUES(?,?)",
                           ("manifest_sha256", hashlib.sha256(canonical(manifest)).hexdigest()))
        connection.execute("CREATE TABLE delivery_history(delivery_id TEXT PRIMARY KEY, recipient TEXT, field TEXT, status TEXT, project TEXT, epoch TEXT)")
        connection.execute("CREATE TABLE deliveries(delivery_id TEXT PRIMARY KEY, recipient TEXT, field TEXT, status TEXT, project TEXT, epoch TEXT)")
        connection.execute("CREATE TABLE released(field TEXT PRIMARY KEY, value TEXT)")
        connection.execute("CREATE TABLE withdrawal_receipts(delivery_id TEXT PRIMARY KEY, status TEXT)")
        connection.execute("CREATE TABLE notice_receipts(recipient TEXT PRIMARY KEY, status TEXT)")
        connection.execute("CREATE TABLE unresolved(delivery_id TEXT PRIMARY KEY)")
        for row in manifest["deliveries"]:
            values = tuple(row[key] for key in ("delivery_id", "recipient", "field", "status", "project", "epoch"))
            connection.execute("INSERT INTO delivery_history VALUES(?,?,?,?,?,?)", values)
            connection.execute("INSERT INTO deliveries VALUES(?,?,?,?,?,?)", values)
        for field in plan["release"]:
            connection.execute("INSERT INTO released VALUES(?,?)", (field, node_values[field]))
        for ident in plan["withdraw"]:
            row = connection.execute("SELECT status FROM deliveries WHERE delivery_id=?", (ident,)).fetchone()
            status = "not-found" if row is None else "not-delivered" if row[0] != "delivered" else "tombstoned"
            if status == "tombstoned":
                connection.execute("DELETE FROM deliveries WHERE delivery_id=?", (ident,))
            connection.execute("INSERT INTO withdrawal_receipts VALUES(?,?)", (ident, status))
        for recipient in plan["notify"]:
            status = "recorded-local" if manifest["consent"].get(recipient, False) else "denied-contact"
            connection.execute("INSERT INTO notice_receipts VALUES(?,?)", (recipient, status))
        for ident in plan["unresolved"]:
            connection.execute("INSERT INTO unresolved VALUES(?)", (ident,))
        connection.commit()
    return {"reopened": True, "artifact": read_artifact(path),
            "boundary": "Synthetic local SQLite effects; tombstones preserve historical delivery and do not undo recipient knowledge."}


def grade_artifact(path, manifest, criterion, knowledge):
    """Independent matrix-based grader; knowledge is host supplied, never plan data."""
    manifest = validate_manifest(manifest)
    _require(knowledge in ("known", "unknown"), "host knowledge state")
    artifact = _bound_artifact(path, manifest)
    actual_forbidden = _matrix_forbidden(manifest, criterion)
    all_sets = [_matrix_forbidden(manifest, candidate) for candidate in CRITERIA]
    if knowledge == "known":
        release_forbidden = repair_forbidden = actual_forbidden
        ambiguous = set()
    else:
        release_forbidden = set.union(*all_sets)
        repair_forbidden = set.intersection(*all_sets)
        ambiguous = release_forbidden - repair_forbidden
    expected_release = set(manifest["requested"]) - release_forbidden
    withdraw, notify, unresolved = set(), set(), set()
    scoped = _scoped_delivered(manifest)
    for row in scoped:
        if row["field"] in repair_forbidden:
            withdraw.add(row["delivery_id"])
            if manifest["consent"].get(row["recipient"], False):
                notify.add(row["recipient"])
            else:
                unresolved.add(row["delivery_id"])
        elif row["field"] in ambiguous:
            unresolved.add(row["delivery_id"])
    released = {row["field"] for row in artifact["released"]}
    remaining = {row["delivery_id"] for row in artifact["remaining"]}
    removed = {row["delivery_id"] for row in manifest["deliveries"]} - remaining
    notices = {row["recipient"] for row in artifact["notices"] if row["status"] == "recorded-local"}
    denied = sorted(row["recipient"] for row in artifact["notices"] if row["status"] == "denied-contact")
    actual_unresolved = {row["delivery_id"] for row in artifact["unresolved"]}
    failures = sorted(row["delivery_id"] for row in artifact["withdrawals"] if row["status"] != "tombstoned")
    source_values = {node["id"]: node["value"] for node in manifest["nodes"]}
    wrong_values = sorted(row["field"] for row in artifact["released"] if source_values.get(row["field"]) != row["value"])
    history_expected = sorted(manifest["deliveries"], key=lambda row: row["delivery_id"])
    history_preserved = artifact["history"] == history_expected
    remaining_preserved = artifact["remaining"] == [row for row in history_expected if row["delivery_id"] not in removed]
    tombstones = {row["delivery_id"] for row in artifact["withdrawals"] if row["status"] == "tombstoned"}
    appropriate = (released == expected_release and removed == withdraw and notices == notify and
                   actual_unresolved == unresolved and not denied and not failures and not wrong_values and
                   history_preserved and remaining_preserved and tombstones == removed)
    actual_historical = {row["delivery_id"] for row in scoped if row["field"] in actual_forbidden}
    return {"knowledge": knowledge, "appropriate_policy": appropriate,
            "actual_unsafe_new_releases": sorted(released & actual_forbidden),
            "actual_forbidden_historical_deliveries": sorted(actual_historical),
            "actual_untombstoned_historical_deliveries": sorted(actual_historical & remaining),
            "appropriate_missing_release": sorted(expected_release - released),
            "unjustified_release": sorted(released - expected_release),
            "full_information_missed_release_secondary": sorted((set(manifest["requested"]) - actual_forbidden) - released),
            "missing_withdrawals": sorted(withdraw - removed), "unexpected_withdrawals": sorted(removed - withdraw),
            "missing_notices": sorted(notify - notices), "unexpected_notices": sorted(notices - notify),
            "denied_contact_attempts": denied, "withdrawal_failed_attempts": failures,
            "missing_unresolved": sorted(unresolved - actual_unresolved),
            "unexpected_unresolved": sorted(actual_unresolved - unresolved),
            "history_preserved": history_preserved, "wrong_release_values": wrong_values,
            "remaining_rows_preserved": remaining_preserved,
            "boundary": "Finite scoped calibration only. Appropriate uncertainty is distinct from actual outcome; no recipient knowledge erasure or model benefit is proved."}


def owner_feedback(path, manifest, criterion, probe_fields):
    """Raw authored owner labels plus actual artifact, never a criterion name/plan."""
    manifest = validate_manifest(manifest)
    _require(len(probe_fields) == 2 and all(field in manifest["requested"] for field in probe_fields), "feedback fields")
    blocked = _matrix_forbidden(manifest, criterion)
    artifact = _bound_artifact(path, manifest)
    released = {row["field"]: row["value"] for row in artifact["released"]}
    rows = []
    for field in probe_fields:
        source_ids = sorted({field} | {edge["target"] for edge in manifest["edges"] if edge["source"] == field})
        rows.append({"field": field, "owner_label": "object" if field in blocked else "accept",
                     "source_ids": source_ids, "artifact": {"released": field in released,
                     "released_value": released.get(field)}})
    return {"project": manifest["project"], "epoch": manifest["epoch"], "assessments": rows,
            "assessment_scope": "Field permissibility labels; an absent release is not invented delivery or harm."}


def identify_from_feedback(manifest, feedback):
    """Authored unchanged generic procedure: infer only a scoped parameter."""
    manifest = validate_manifest(manifest)
    if feedback.get("project") != manifest["project"] or feedback.get("epoch") != manifest["epoch"]:
        return None
    compatible = []
    for criterion in CRITERIA:
        blocked = _walk_forbidden(manifest, criterion)
        if all(row["owner_label"] == ("object" if row["field"] in blocked else "accept")
               for row in feedback["assessments"]):
            compatible.append(criterion)
    return compatible[0] if len(compatible) == 1 else None
