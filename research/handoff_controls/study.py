"""Offline generic-file control and fixed-capacity boundary replay. No models."""
import hashlib
import json
from pathlib import Path
import random
import string
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/"examples"))
sys.path.insert(0, str(HERE.parent/"handoff_repair"))
sys.path.insert(0, str(HERE.parent/"transfer_calibration_v3"))
from continuity import Event
from durable import Hold, canonical, event_operation
from tasks import receiver_prompt
from transport import VERSION, pack_history, unpack_history

CAPACITY = 3200
PIN_BYTES = 64
SCENARIOS = (("base", 0, False), ("repeated-log", 8, False), ("variable-log", 8, True))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_pins():
    names = ["research/handoff_controls/study.py", "research/handoff_controls/test_controls.py",
             "research/handoff_repair/transport.py", "research/handoff_repair/cases.json",
             "research/transfer_calibration_v3/tasks.py", "examples/continuity.py", "examples/durable.py"]
    return {name:sha((ROOT/name).read_bytes()) for name in names}


def extended(case, count, variable):
    ops = list(case["history"])
    rng = random.Random(7419+case["seed"])
    for index in range(count):
        content = ("ordinary repeated log line; "*30)[:512]
        if variable:
            content = "".join(rng.choice(string.ascii_letters+string.digits) for _ in range(512))
        event = Event("control-log-"+str(index), "release-engineer", "main", "observation",
                      "coordination", "recorded", content, "coordination")
        ops.append(event_operation(event))
    return {**case, "history":ops}


def derive():
    rows = []
    material = json.loads((HERE.parent/"handoff_repair/cases.json").read_text())
    with tempfile.TemporaryDirectory(prefix="generic-journal-control-") as work:
        folder = Path(work)
        for entry in material:
            for scenario, count, variable in SCENARIOS:
                case = extended(entry["source"], count, variable)
                body = {"schema":VERSION, "branch":"main", "scope":case["scope"],
                        "stream":"fixture-source", "history":case["history"]}
                raw = canonical(body)
                path = folder/(case["id"]+"-"+scenario+".json")
                with path.open("xb") as file:
                    file.write(raw)
                delivered = path.read_bytes()
                if sha(delivered) != sha(raw):
                    raise ValueError("generic-file-readback-drift")
                generic = json.loads(delivered)
                generic_prompt = receiver_prompt({**case, "history":generic["history"]}, full=True)
                row = {"case":case["id"], "scenario":scenario, "generic_file_bytes":len(delivered)+64,
                       "generic_history_exact":generic["history"] == case["history"],
                       "generic_within_channel":len(delivered)+64 <= CAPACITY,
                       "full_prompt_sha256":sha(generic_prompt.encode())}
                try:
                    wire = pack_history(case["history"], stream="fixture-source", branch="main",
                                        scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
                    restored = unpack_history(wire, expected_sha256=sha(wire), branch="main",
                                              scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
                    exact_prompt = receiver_prompt({**case, "history":restored["history"]}, full=True)
                    if canonical(restored) != delivered or exact_prompt != generic_prompt:
                        raise ValueError("information-equivalent-control-drift")
                    row.update(exact_admitted=True, exact_bytes=len(wire)+64,
                               decoded_bytes_equal=True, receiver_prompt_equal=True)
                except Hold as error:
                    if str(error) != "complete-handoff-exceeds-capacity":
                        raise
                    row.update(exact_admitted=False, hold_reason=str(error),
                               decoded_bytes_equal=None, receiver_prompt_equal=None)
                rows.append(row)
    summary = []
    for scenario, _count, _variable in SCENARIOS:
        group = [row for row in rows if row["scenario"] == scenario]
        summary.append({"scenario":scenario, "cases":len(group),
                        "generic_exact_histories":sum(row["generic_history_exact"] for row in group),
                        "generic_within_3200_bytes":sum(row["generic_within_channel"] for row in group),
                        "exact_admitted":sum(row["exact_admitted"] for row in group),
                        "same_receiver_prompt":sum(row["receiver_prompt_equal"] is True for row in group),
                        "generic_byte_range":[min(row["generic_file_bytes"] for row in group),
                                              max(row["generic_file_bytes"] for row in group)]})
    return {"schema":"handoff-file-control/1", "kind":"post-cohort-deterministic-replay", "llm_calls":0,
            "capacity":CAPACITY, "external_pin_bytes":PIN_BYTES, "input_sha256":source_pins(),
            "summary":summary, "cases":rows,
            "scope":"Information/byte parity and finite codec capacity; no generic-file model performance was sampled."}


if __name__ == "__main__":
    result = derive()
    (HERE/"results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"summary":result["summary"], "llm_calls":0}))
