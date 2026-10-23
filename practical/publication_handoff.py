"""Continue real repository checks in a fresh process; detect stale evidence.

Explicitly requires a shared permitted checkout. Creates only owned temporary
SQLite/files, runs fixed offline gates, and never executes restored commands.
No model, network, deployment or external publication is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"examples"))
sys.path.insert(0, str(ROOT/"research/handoff_repair"))
from continuity import Event
from durable import DEFAULT, Hold, Journal, ZERO, canonical, digest, event_operation, operation
from transport import context_from_handoff, export_journal

CAPACITY = 16384
GATES = (("-m", "unittest", "discover", "-s", "research/handoff_repair", "-q"),
         ("-m", "unittest", "discover", "-s", "research/handoff_controls", "-q"),
         ("-m", "unittest", "discover", "-s", "research", "-p", "test_handoff_repair_integrity.py", "-q"),
         ("-O", "research/verify_handoff_repair.py"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def input_paths():
    paths = {"practical/publication_handoff.py", "research/verify_handoff_repair.py",
             "research/test_handoff_repair_integrity.py", "research/handoff_controls/results.json"}
    for folder in ("examples", "research/handoff_repair", "research/handoff_controls"):
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).glob("*.py"))
    frozen = json.loads((ROOT/"research/handoff_repair/freeze.json").read_text())
    for path in frozen["input_sha256"]:
        paths.add(str((ROOT/"research/handoff_repair"/path).resolve().relative_to(ROOT)))
    for name in ("freeze.json", "cases.json", "completion.json", "episodes.json", "results.json", "responses.jsonl.gz"):
        paths.add("research/handoff_repair/"+name)
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/"research/handoff_repair/artifacts").rglob("*") if p.is_file())
    paths.update(str(p.relative_to(ROOT)) for p in (ROOT/"examples").glob("*.json"))
    return sorted(paths)


def file_sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def check(wire, pin, scope, source_root):
    ctx = context_from_handoff(wire, expected_sha256=pin, branch="main", scope=scope,
                               topic="publication-gates", capacity=CAPACITY-64, context_budget=65536)
    if ctx["view"]["status"] != "supported":
        raise Hold("gates-not-supported")
    records = [json.loads(e["text"]) for e in ctx["evidence"] if e["kind"] == "observation"]
    manifests = [r for r in records if r.get("kind") == "source"]
    gates = [r for r in records if r.get("kind") == "gate"]
    if len(manifests) != 1 or len(gates) != len(GATES):
        raise Hold("incomplete-gate-evidence")
    if {g["index"] for g in gates} != set(range(len(GATES))):
        raise Hold("gate-identity-mismatch")
    for gate in gates:
        if gate["command"] != ["python3", *GATES[gate["index"]]] or gate["exit_code"] != 0:
            raise Hold("gate-command-or-result-mismatch")
    manifest = manifests[0]["files"]
    if type(manifest) is not dict or not manifest or len(manifest) > 512:
        raise Hold("invalid-source-manifest")
    root = source_root.resolve()
    changed = []
    for name, expected in manifest.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise Hold("source-path-escape")
        path = (root/name).resolve()
        if not path.is_relative_to(root):
            raise Hold("source-path-escape")
        if not path.is_file() or file_sha(path) != expected:
            changed.append(name)
    return {"state":"stale-evidence" if changed else "current-for-listed-gates",
            "source_files_checked":len(manifest), "changed":changed,
            "gate_count":len(gates), "model_calls":0,
            "scope":"Historical process exits tied to current listed bytes; no independent execution attestation or publication authorization."}


def child(wire_path, pin, scope, source_root):
    return subprocess.run([sys.executable, str(Path(__file__).resolve()), "--check", str(wire_path),
                           "--pin", pin, "--scope", scope, "--root", str(source_root)],
                          capture_output=True, timeout=30)


def demonstrate():
    sources = {name:file_sha(ROOT/name) for name in input_paths()}
    scope = "candidate-"+digest(sources)[:20]
    reports = []
    for index, args in enumerate(GATES):
        run = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=60)
        reports.append({"kind":"gate", "index":index, "command":["python3", *args],
                        "exit_code":run.returncode, "stdout":run.stdout, "stderr":run.stderr})
        if run.returncode:
            raise Hold("actual-gate-failed:"+str(index))
    if sources != {name:file_sha(ROOT/name) for name in sources}:
        raise Hold("source-changed-during-gates")
    with tempfile.TemporaryDirectory(prefix="publication-handoff-demo-") as work:
        folder = Path(work)
        journal = Journal(folder/"owned.sqlite", create=True)
        tail = journal.append(operation("init", "init", actor="repository-reviewer", orientation=DEFAULT), expected=ZERO)
        basis = []
        for index, record in enumerate([{"kind":"source", "files":sources}, *reports]):
            event = Event("evidence-"+str(index), "repository-reviewer", "main", "observation",
                          "publication-gates", "recorded", canonical(record).decode(), scope)
            tail = journal.append(event_operation(event), expected=tail["head"])
            basis.append(event.id)
        claim = Event("gate-conclusion", "repository-reviewer", "main", "claim", "publication-gates",
                      "supported", "Listed offline gates returned zero for these exact input bytes.", scope, tuple(basis))
        journal.append(event_operation(claim), expected=tail["head"])
        wire, tail = export_journal(journal, branch="main", scope=scope, capacity=CAPACITY-64)
        wire_path = folder/"wire.json"
        wire_path.write_bytes(wire)
        pin = sha(wire)
        current = child(wire_path, pin, scope, ROOT)
        if current.returncode != 0:
            raise Hold("fresh-current-consumer-failed")
        current_view = json.loads(current.stdout)
        # Deliberately altered owned copy; the user's checkout stays untouched.
        copied = folder/"changed-copy"
        for name in sources:
            dest = copied/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, dest)
        target = copied/"research/handoff_repair/transport.py"
        target.write_bytes(target.read_bytes()+b"\n# controlled drift witness\n")
        drifted = child(wire_path, pin, scope, copied)
        if drifted.returncode != 3:
            raise Hold("stale-source-not-rejected")
        drift_view = json.loads(drifted.stdout)
        if drift_view["changed"] != ["research/handoff_repair/transport.py"]:
            raise Hold("wrong-drift-diagnosis")
        return {"schema":"real-repository-gate-handoff/1", "kind":"actual-offline-gates-and-controlled-drift",
                "scope":scope, "capacity":CAPACITY, "wire_and_pin_bytes":len(wire)+64,
                "source_sha256":sources, "gate_runs":reports, "wire_sha256":pin,
                "wire_utf8":wire.decode("ascii"),
                "unchanged_consumer":{"exit_code":current.returncode, "result":current_view},
                "changed_copy_consumer":{"exit_code":drifted.returncode, "result":drift_view},
                "model_calls":0, "live_house_deployment":False,
                "limits":["shared checkout required", "controlled drift, not a natural incident",
                          "trusted caller records process exits", "not independent attestation",
                          "no real publication action or subjective-state measurement"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--pin")
    parser.add_argument("--scope")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.check:
        with args.check.open("rb") as source:
            wire = source.read(CAPACITY-64+1)
        value = check(wire, args.pin, args.scope, args.root)
        print(json.dumps(value))
        return 3 if value["state"] == "stale-evidence" else 0
    report = demonstrate()
    if args.output:
        with args.output.open("x") as out:
            out.write(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"current_consumer":report["unchanged_consumer"]["result"]["state"],
                      "changed_copy":report["changed_copy_consumer"]["result"]["state"],
                      "source_files":len(report["source_sha256"]), "wire_and_pin_bytes":report["wire_and_pin_bytes"],
                      "model_calls":0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
