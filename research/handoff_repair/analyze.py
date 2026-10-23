"""Offline reconstruction of actual transport, prompts, scores and plan files."""
import gzip
import hashlib
import json
from pathlib import Path

from run import (ARMS, CAPACITY, HERE, PIN_BYTES, ROOT, brute, field, pins,
                 planning_success, receiver_prompt, recursive, schedule, score,
                 sender_prompt, sources, stored_note)
from transport import pack_history, unpack_history


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def artifact(base, item, raw, folder, name):
    relative = "artifacts/"+folder+"/"+name
    require(item == {"path":relative, "sha256":sha(raw), "bytes":len(raw)}, "artifact-descriptor-drift")
    require((base/relative).read_bytes() == raw, "artifact-content-drift")


def derive(base=HERE):
    frozen = json.loads((base/"freeze.json").read_text())
    complete = json.loads((base/"completion.json").read_text())
    require(frozen["input_sha256"] == pins(), "frozen-source-drift")
    require(frozen["schedule"] == schedule(), "schedule-drift")
    require(complete["freeze_sha256"] == sha((base/"freeze.json").read_bytes()), "freeze-drift")
    require(complete["input_pins_after"] == pins() and complete["source_unchanged"] is True, "post-run-source-drift")
    raw = gzip.decompress((base/"responses.jsonl.gz").read_bytes())
    require(sha(raw) == complete["raw_sha256"], "raw-archive-drift")
    rows = [json.loads(line) for line in raw.splitlines()]
    require(len(rows) == complete["captured_calls"] <= frozen["maximum_model_calls"], "call-count-drift")
    indexed = {}
    for row in rows:
        key = (row["case"], row["arm"], row["stage"])
        require(key not in indexed, "duplicate-model-call")
        indexed[key] = row
        require(row["prompt_sha256"] == sha(row["prompt"].encode()), "prompt-digest-drift")
        completed = [e for e in row["events"] if e.get("type") == "turn.completed"]
        if completed:
            require(row.get("usage", {}) == completed[-1].get("usage", {}), "native-usage-drift")
        terminal = bool(completed and row.get("exit_code") == 0 and not row.get("tools")
                        and not row.get("unparsed_stdout") and not row.get("error")
                        and not any(e.get("type") in ("turn.failed", "error") for e in row["events"]))
        require(row["terminal"] is terminal, "terminal-classification-drift")
    material = json.loads((base/"cases.json").read_text())
    require([x["source"] for x in material] == sources(), "materialized-source-drift")
    source = {x["source"]["id"]:x["source"] for x in material}
    for entry in material:
        truth = brute(entry["source"])
        require(entry["oracle"] == truth, "oracle-drift")
        require({k:truth[k] for k in recursive(entry["source"])} == recursive(entry["source"]), "solver-disagreement")
    episodes = json.loads((base/"episodes.json").read_text())
    require([[e["case"], e["arm"]] for e in episodes] == schedule(), "episode-coverage-drift")
    require(len(episodes) == complete["episodes"] == frozen["episodes"], "episode-count-drift")
    used, checked = set(), []
    for episode in episodes:
        case, arm = source[episode["case"]], episode["arm"]
        folder = case["id"]+"-"+arm
        require(episode["seed"] == case["seed"] and episode["variant"] == case["variant"], "episode-source-drift")
        arts = episode["artifacts"]
        if arm == "freeform":
            key = (case["id"], arm, "sender")
            sent = indexed[key]; used.add(key)
            require(sent["prompt"] == sender_prompt(case, 12000), "sender-prompt-drift")
            whole = field(sent)
            if whole is None:
                require(episode["failure_stage"] == "sender" and episode["primary"] is False
                        and episode["planning_only"] is False and not arts
                        and episode["plan_effect"] == {"written":False}, "sender-failure-drift")
                checked.append({"case":case["id"], "seed":case["seed"], "arm":arm,
                                "primary":False, "planning_only":False, "failure_stage":"sender"})
                continue
            note, truncated = stored_note(whole, CAPACITY)
            require(len(arts) == 2, "freeform-artifact-count")
            artifact(base, arts[0], whole.encode(), folder, "whole.txt")
            artifact(base, arts[1], note.encode(), folder, "retained.txt")
            require((episode["whole_bytes"], episode["retained_bytes"], episode["truncated"])
                    == (len(whole.encode()), len(note.encode()), truncated), "loss-channel-drift")
            prompt = receiver_prompt(case, note, truncated=truncated)
        else:
            require(arm == "exact", "unknown-arm")
            wire = pack_history(case["history"], stream="fixture-source", branch="main",
                                scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
            pin = sha(wire)
            if episode["failure_stage"] == "transport":
                require(episode["primary"] is False and episode["planning_only"] is False
                        and episode["plan_effect"] == {"written":False}
                        and type(episode.get("transport_error")) is dict, "transport-failure-drift")
                require(len(arts) in (0, 1, 2, 3), "transport-failure-artifacts")
                if len(arts) >= 1:
                    artifact(base, arts[0], wire, folder, "wire.json")
                if len(arts) >= 2:
                    artifact(base, arts[1], pin.encode(), folder, "wire.sha256")
                if len(arts) >= 3:
                    restored = (base/arts[2]["path"]).read_bytes()
                    artifact(base, arts[2], restored, folder, "restored.json")
                checked.append({"case":case["id"], "seed":case["seed"], "arm":arm,
                                "primary":False, "planning_only":False, "failure_stage":"transport"})
                continue
            body = unpack_history(wire, expected_sha256=pin, branch="main",
                                  scope=case["scope"], capacity=CAPACITY-PIN_BYTES)
            restored = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            require(len(arts) == 3, "exact-artifact-count")
            artifact(base, arts[0], wire, folder, "wire.json")
            artifact(base, arts[1], pin.encode(), folder, "wire.sha256")
            artifact(base, arts[2], restored, folder, "restored.json")
            require(body["history"] == case["history"], "restore-drift")
            require(episode["retained_bytes"] == len(wire)+64 <= CAPACITY, "transport-budget-drift")
            require(episode["exact_recovery"] is True and episode["full_history_prompt_parity"] is True
                    and episode["decoder_exit_code"] == 0, "decoder-observation-drift")
            prompt = receiver_prompt({**case, "history":body["history"]}, full=True)
            require(prompt == receiver_prompt(case, full=True), "source-to-prompt-drift")
        key = (case["id"], arm, "receiver")
        received = indexed[key]; used.add(key)
        require(received["prompt"] == prompt, "receiver-prompt-drift")
        evaluated = score(case, received["response"], received["terminal"])
        primary = evaluated["optimal"]
        planning = planning_success(evaluated, case)
        require(episode["score"] == evaluated and episode["primary"] is primary
                and episode["planning_only"] is planning, "episode-score-drift")
        require(episode["failure_stage"] == (None if received["terminal"] else "receiver"), "receiver-failure-drift")
        if primary:
            answer = json.loads(received["response"])
            plan = json.dumps({"case":case["id"], "plan":answer["plan"], "evidence":answer["evidence"]},
                              sort_keys=True, separators=(",", ":")).encode()
            effect = episode["plan_effect"]
            require(effect.get("written") is True, "missing-plan-effect")
            artifact(base, {k:v for k,v in effect.items() if k != "written"}, plan, folder, "plan.json")
        else:
            require(episode["plan_effect"] == {"written":False}, "unearned-plan-effect")
        checked.append({"case":case["id"], "seed":case["seed"], "arm":arm,
                        "primary":primary, "planning_only":planning,
                        "failure_stage":episode["failure_stage"], "retained_bytes":episode["retained_bytes"],
                        "score":evaluated})
    require(used == set(indexed), "unexpected-or-missing-calls")
    summary = []
    for arm in ARMS:
        eps = [e for e in checked if e["arm"] == arm]
        calls = [r for r in rows if r["arm"] == arm]
        successes = sum(e["primary"] for e in eps)
        usage = {k:sum(r.get("usage", {}).get(k, 0) for r in calls)
                 for k in ("input_tokens", "cached_input_tokens", "output_tokens")}
        summary.append({"arm":arm, "episodes":len(eps), "fully_traced_optimal":successes,
                        "planning_only":sum(e["planning_only"] for e in eps),
                        "failed_stages":sum(e["failure_stage"] is not None for e in eps),
                        "calls":len(calls), "native_usage":usage,
                        "input_tokens_per_completion":usage["input_tokens"]/successes if successes else None,
                        "retained_byte_range":[min(e.get("retained_bytes", 0) for e in eps),
                                               max(e.get("retained_bytes", 0) for e in eps)]})
    by = {(e["case"], e["arm"]):e for e in checked}
    wins = losses = ties = 0
    for case in sources():
        a, b = by[(case["id"], "exact")]["primary"], by[(case["id"], "freeform")]["primary"]
        wins += a > b; losses += a < b; ties += a == b
    return {"schema":"handoff-repair-results/1", "captured_calls":len(rows), "episodes":len(checked),
            "summary":summary, "paired_exact_minus_freeform":{"wins":wins,"losses":losses,"ties":ties},
            "source_clusters":[{"seed":seed, **{arm:sum(e["primary"] for e in checked
                                       if e["seed"] == seed and e["arm"] == arm) for arm in ARMS}}
                                for seed in sorted({e["seed"] for e in checked})],
            "raw_sha256":sha(raw), "source_commit":complete["source_commit"],
            "wall_seconds":complete["wall_seconds"],
            "scope":"Conventional lossless host transport on eight new instances of one familiar task class; no reading-effect or live House benefit claim."}


if __name__ == "__main__":
    result = derive()
    (HERE/"results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result))
