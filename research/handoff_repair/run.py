"""Explicit prospective calls for the registered transport repair comparison."""
import concurrent.futures
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "transfer_calibration_v3"))
from tasks import (brute, make_case, planning_success, receiver_prompt, recursive,
                   score, sender_prompt, stored_note)
sys.path.insert(0, str(HERE.parent / "gpt_profile_pilot_v2"))
# Load this exact previously inspected adapter; avoid importing this run.py again.
import importlib.util
_spec = importlib.util.spec_from_file_location("prior_gpt_adapter", HERE.parent / "gpt_profile_pilot_v2/run.py")
_adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adapter)
invoke, command = _adapter.invoke, _adapter.command
from transport import pack_history

SEEDS = (4013, 4142, 4307, 4496)
ARMS = ("freeform", "exact")
CAPACITY = 3200
PIN_BYTES = 64
LOCK = threading.Lock()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sources():
    return [make_case(seed, variant, "repair") for seed in SEEDS for variant in (0, 1)]


def schedule():
    values = [[c["id"], arm] for c in sources() for arm in ARMS]
    random.Random(231023).shuffle(values)
    return values


def pins():
    names = ["PROTOCOL.md", "run.py", "analyze.py", "test_study.py", "transport.py",
             "test_transport.py", "cases.json", "../transfer_calibration_v3/tasks.py",
             "../../examples/continuity.py", "../../examples/durable.py",
             "../gpt_profile_pilot_v2/run.py", "../gpt_profile_pilot_v2/design.py",
             "../participation_pilot/design.py"]
    return {p: sha((HERE/p).read_bytes()) for p in names}


def freeze():
    if (HERE/"freeze.json").exists():
        raise ValueError("already-frozen")
    material = []
    for case in sources():
        oracle = brute(case)
        if {k: oracle[k] for k in recursive(case)} != recursive(case):
            raise ValueError("solver-disagreement")
        material.append({"source": case, "oracle": oracle})
    (HERE/"cases.json").write_text(json.dumps(material, indent=2)+"\n")
    frozen = {"schema":"handoff-repair-freeze/1", "created_at":datetime.now(timezone.utc).isoformat(),
              "input_sha256":pins(), "schedule":schedule(), "requested_model":"gpt-6.1-sol",
              "reasoning_effort":"high", "command_template":command("{isolated-directory}"),
              "capacity":CAPACITY, "external_pin_bytes":PIN_BYTES, "seeds":list(SEEDS),
              "episodes":16, "maximum_model_calls":24, "repetitions":1,
              "independent_registration":False, "new_task_families":False}
    with (HERE/"freeze.json").open("x") as f:
        f.write(json.dumps(frozen, indent=2)+"\n")
    print(json.dumps({"frozen":True, "episodes":16, "maximum_model_calls":24}))


def field(row):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate-key")
            value[key] = item
        return value
    try:
        value = json.loads(row["response"], object_pairs_hook=unique)
        if (row["terminal"] and type(value) is dict and set(value) == {"handoff"}
                and type(value["handoff"]) is str and len(value["handoff"].encode()) <= 12000):
            return value["handoff"]
    except (ValueError, TypeError, UnicodeError):
        pass
    return None


def artifact(folder, name, raw):
    with (folder/name).open("xb") as f:
        f.write(raw)
    if (folder/name).read_bytes() != raw:
        raise ValueError("artifact-readback")
    return {"path":str((folder/name).relative_to(HERE)), "sha256":sha(raw), "bytes":len(raw)}


def run():
    frozen = json.loads((HERE/"freeze.json").read_text())
    if frozen["input_sha256"] != pins() or frozen["schedule"] != schedule():
        raise ValueError("frozen-input-drift")
    paths = [str((HERE/p).resolve().relative_to(ROOT)) for p in frozen["input_sha256"]]
    paths.append(str((HERE/"freeze.json").relative_to(ROOT)))
    if subprocess.check_output(["git", "status", "--porcelain", "--", *paths], cwd=ROOT):
        raise ValueError("inputs-not-committed")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output = (HERE/"responses.jsonl").open("x")
    indexed = {c["id"]: c for c in sources()}
    rows, began = [], time.perf_counter()

    def target(case, arm, stage, prompt):
        observed = invoke(prompt)
        row = {"case":case["id"], "arm":arm, "stage":stage,
               "prompt":prompt, "prompt_sha256":sha(prompt.encode()), **observed}
        with LOCK:
            rows.append(row)
            output.write(json.dumps(row, ensure_ascii=False)+"\n")
            output.flush()
            print(json.dumps({"captured":len(rows), "maximum":24, "case":case["id"],
                              "arm":arm, "stage":stage}), flush=True)
        return row

    def episode(spec):
        cid, arm = spec
        case = indexed[cid]
        folder = HERE/"artifacts"/(cid+"-"+arm)
        folder.mkdir(parents=True, exist_ok=False)
        result = {"case":cid, "seed":case["seed"], "variant":case["variant"], "arm":arm,
                  "primary":False, "planning_only":False, "failure_stage":None,
                  "artifacts":[], "plan_effect":{"written":False}}
        if arm == "freeform":
            sent = target(case, arm, "sender", sender_prompt(case, 12000))
            whole = field(sent)
            if whole is None:
                return {**result, "failure_stage":"sender"}
            note, truncated = stored_note(whole, CAPACITY)
            result["artifacts"].append(artifact(folder, "whole.txt", whole.encode()))
            result["artifacts"].append(artifact(folder, "retained.txt", note.encode()))
            result.update(whole_bytes=len(whole.encode()), retained_bytes=len(note.encode()), truncated=truncated)
            prompt = receiver_prompt(case, note, truncated=truncated)
        else:
            # Neither the future event nor oracle enters this adapter.
            try:
                wire = pack_history(case["history"], stream="fixture-source", branch="main",
                                    scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
                pin = sha(wire)
                result["artifacts"].append(artifact(folder, "wire.json", wire))
                result["artifacts"].append(artifact(folder, "wire.sha256", pin.encode()))
                restored = subprocess.run([sys.executable, str(HERE/"transport.py"),
                    "--expected-sha256", pin, "--branch", "main", "--scope", case["scope"],
                    "--capacity", str(CAPACITY-PIN_BYTES)], input=(folder/"wire.json").read_bytes(),
                    capture_output=True, timeout=10, check=True)
                body = json.loads(restored.stdout)
                result["artifacts"].append(artifact(folder, "restored.json", restored.stdout))
                if body["history"] != case["history"]:
                    raise ValueError("restored-source-drift")
                delivered = {**case, "history":body["history"]}
                prompt = receiver_prompt(delivered, full=True)
                if prompt != receiver_prompt(case, full=True):
                    raise ValueError("full-history-prompt-drift")
                result.update(retained_bytes=len(wire)+len(pin), exact_recovery=True,
                              full_history_prompt_parity=True, decoder_exit_code=restored.returncode)
            except Exception as exc:
                return {**result, "failure_stage":"transport", "transport_error":{
                    "kind":type(exc).__name__, "message":str(exc),
                    "stderr":getattr(exc, "stderr", b"").decode(errors="replace")[-2000:]
                             if isinstance(getattr(exc, "stderr", None), bytes) else ""}}
        received = target(case, arm, "receiver", prompt)
        evaluated = score(case, received["response"], received["terminal"])
        result.update(score=evaluated, primary=evaluated["optimal"],
                      planning_only=planning_success(evaluated, case))
        if evaluated["optimal"]:
            answer = json.loads(received["response"])
            raw = json.dumps({"case":cid, "plan":answer["plan"], "evidence":answer["evidence"]},
                             sort_keys=True, separators=(",", ":")).encode()
            result["plan_effect"] = {"written":True, **artifact(folder, "plan.json", raw)}
        if not received["terminal"]:
            result["failure_stage"] = "receiver"
        return result

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            episodes = list(pool.map(episode, frozen["schedule"]))
        raw = (HERE/"responses.jsonl").read_bytes()
        (HERE/"responses.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
        (HERE/"episodes.json").write_text(json.dumps(episodes, indent=2)+"\n")
        completion = {"schema":"handoff-repair-completion/1", "source_commit":commit,
                      "freeze_sha256":sha((HERE/"freeze.json").read_bytes()), "raw_sha256":sha(raw),
                      "captured_calls":len(rows), "episodes":len(episodes),
                      "input_pins_after":pins(), "source_unchanged":pins()==frozen["input_sha256"],
                      "wall_seconds":round(time.perf_counter()-began, 3),
                      "completed_at":datetime.now(timezone.utc).isoformat()}
        (HERE/"completion.json").write_text(json.dumps(completion, indent=2)+"\n")
        print(json.dumps(completion), flush=True)
    finally:
        output.close()


if __name__ == "__main__":
    if sys.argv[1:] == ["freeze"]:
        freeze()
    elif sys.argv[1:] == ["run"]:
        run()
    else:
        raise SystemExit("use freeze or run")
