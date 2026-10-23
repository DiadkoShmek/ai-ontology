"""Verify generic-file replay and the actual retained repository handoff bytes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"research/handoff_controls"))
from study import derive
sys.path.insert(0, str(ROOT/"practical"))
from publication_handoff import CAPACITY, ROOT as SUBJECT, check


def main():
    computed = derive()
    saved = json.loads((ROOT/"research/handoff_controls/results.json").read_text())
    if saved != computed:
        raise ValueError("file-control-results-drift")
    practical = json.loads((ROOT/"practical/publication-handoff-results.json").read_text())
    wire = practical["wire_utf8"].encode("ascii")
    if (hashlib.sha256(wire).hexdigest() != practical["wire_sha256"]
            or len(wire)+64 != practical["wire_and_pin_bytes"]
            or practical["capacity"] != CAPACITY):
        raise ValueError("practical-wire-drift")
    current = check(wire, practical["wire_sha256"], practical["scope"], SUBJECT)
    if current != practical["unchanged_consumer"]["result"] or practical["unchanged_consumer"]["exit_code"] != 0:
        raise ValueError("practical-source-or-result-drift")
    for name, expected in practical["source_sha256"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError("practical-listed-source-drift:"+name)
    changed = practical["changed_copy_consumer"]
    if (changed["exit_code"] != 3 or changed["result"]["state"] != "stale-evidence"
            or changed["result"]["changed"] != ["research/handoff_repair/transport.py"]):
        raise ValueError("controlled-drift-record-mismatch")
    print(json.dumps({"generic_control_consistent":True, "practical_wire_restored":True,
                      "source_files_checked":current["source_files_checked"], "model_calls":0,
                      "scope":"Exact retained bytes, current listed files and captured records; no independent process attestation."}))


if __name__ == "__main__":
    main()
