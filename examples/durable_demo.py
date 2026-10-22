"""Disposable local demonstration; no provider calls and no persistent service."""
import json
from pathlib import Path
import tempfile

from continuity import read_fixture
from durable import DEFAULT, ZERO, Journal, Hold, event_operation, operation
from agent_cycle import ReplayModel, run_turn


def demonstrate():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "continuity.sqlite"
        j = Journal(path, create=True)
        tail = j.append(operation("genesis", "init", actor="iris", orientation=DEFAULT), expected=ZERO)
        events = read_fixture()
        for e in events[:2]:
            tail = j.append(event_operation(e), expected=tail["head"])
        before = j.context("main", "cache-current", "updates-A")
        for e in events[2:]:
            tail = j.append(event_operation(e), expected=tail["head"])
        restarted = Journal(path)
        after = restarted.context("main", "cache-current", "updates-A", anchor=tail)
        turn = run_turn(restarted, turn_id="turn-1", branch="main", topic="cache-current",
            scope="updates-A", question="What changed and what remains unknown?",
            model=ReplayModel({"text":"The claim is refuted for updates-A. Other scopes remain untested.",
                               "stance":"answer", "cites":["c2","o2"]}),
            expected_model_id="authored-replay/1", anchor=tail)
        return {"kind":"runtime-demonstration-with-authored-model-replay", "llm_trials":0,
                "before":before["view"], "after_reopen":after["view"],
                "orientation_recovered":after["profile"] == DEFAULT,
                "context_bytes":len(json.dumps(after,ensure_ascii=False).encode()),
                "decision":turn}


if __name__ == "__main__":
    print(json.dumps(demonstrate(), ensure_ascii=False, indent=2))
