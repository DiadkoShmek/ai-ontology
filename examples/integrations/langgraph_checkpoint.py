"""Emit an authored in-memory LangGraph native export to stdout.

No models, network, external checkpoint capture or disk durability claim.
The runtime guard covers this known Python example, not arbitrary native code.
"""

import importlib.metadata
import os
import sys
from pathlib import Path


def guard_runtime():
    """Guard this known Python probe, not an arbitrary native-code sandbox."""
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    sys.dont_write_bytecode = True

    def guard(event, args):
        if event.startswith("socket."):
            raise PermissionError("network disabled for native bridge proof")
        if event == "open" and len(args) > 2 and type(args[2]) is int and args[2] & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError("filesystem writes disabled for native bridge proof")
        if event in ("os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.link", "os.symlink",
                     "os.truncate", "subprocess.Popen", "os.system"):
            raise PermissionError("persistent/process side effects disabled for native bridge proof")
    sys.addaudithook(guard)


def capture_native():
    """Actual StateGraph execution with ordinary app state, no ontology outputs."""
    from typing import TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import InMemorySaver
    from audit.adapters.langgraph_checkpoint import SCHEMA

    class State(TypedDict):
        query: str
        text: str
        answer: str

    def read_document(state):
        return {"text": "Authored fixture: report revision 2 has status draft."}

    def answer(state):
        return {"answer": state["text"].split(" has status ")[1].rstrip(".")}

    builder = StateGraph(State)
    builder.add_node("read_document", read_document)
    builder.add_node("answer", answer)
    builder.add_edge(START, "read_document")
    builder.add_edge("read_document", "answer")
    builder.add_edge("answer", END)
    app = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "authored-checkpoint-demo"}}
    result = app.invoke({"query": "What is the status?"}, config, durability="sync")
    if result["answer"] != "draft":
        raise AssertionError("authored native execution changed")

    def path_lists(value):
        return [path_lists(child) for child in value] if type(value) is tuple else value

    snapshots = []
    for snapshot in app.get_state_history(config):
        snapshots.append({
            "values": snapshot.values, "next": list(snapshot.next), "config": snapshot.config,
            "metadata": snapshot.metadata, "created_at": snapshot.created_at,
            "parent_config": snapshot.parent_config,
            "tasks": [{"id": task.id, "name": task.name, "path": path_lists(task.path),
                       "error": task.error, "interrupts": list(task.interrupts),
                       "state": task.state, "result": task.result} for task in snapshot.tasks],
            "interrupts": list(snapshot.interrupts),
        })
    producer = {name: importlib.metadata.version(name) for name in (
        "langgraph", "langgraph-checkpoint", "langchain-core")}
    return {"schema": SCHEMA, "producer": producer, "snapshots": snapshots}


def main():
    guard_runtime()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from audit.adapters.langgraph_checkpoint import encode_export
    try:
        raw = encode_export(capture_native())
    except ModuleNotFoundError as exc:
        print("Optional LangGraph example dependency missing: " + str(exc), file=sys.stderr)
        return 2
    # Exactly the native export: no proof wrapper, private path, inferred graph,
    # model output or automatic persistent file. Redirect only to a local file.
    sys.stdout.buffer.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
