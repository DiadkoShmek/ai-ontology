"""Check the editorial status ledger, not the truth of its claims. No network."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INITIAL_DOCUMENT_SHA256 = "cf279d50ba6b174b66dd55ae7be34d0363f6945217c6e48e61b6263186a73b2a"
INITIAL_STATUS = (
    "implemented", "conditional", "unsupported", "observed", "not-established",
    "refuted", "observed", "proposed", "conditional", "not-claimed", "not-established",
)
STATUSES = frozenset(INITIAL_STATUS) | {"withdrawn", "superseded"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def version(value):
    require(bool(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", value)),
            "invalid publication edition")
    return tuple(map(int, value.split(".")))


def rows(document, header, count):
    lines = document.splitlines()
    require(lines.count(header) == 1, "missing or duplicated ledger table")
    start = lines.index(header) + 2
    answer = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        row = tuple(part.strip().strip("`") for part in line.strip("|").split("|"))
        require(len(row) == count, "malformed ledger row")
        answer.append(row)
    require(bool(answer), "empty ledger table")
    return answer


def parse(document):
    claims = rows(document, "| ID | Status | Claim | Evidence and reproduction | Status and boundary |", 5)
    history = rows(document, "| ID | Edition | Status | Reason | Evidence |", 5)
    heads = {}
    for claim_id, status, *text in claims:
        require(bool(re.fullmatch(r"C[0-9]{2,}", claim_id)) and claim_id not in heads, "invalid or duplicate claim ID")
        require(status in STATUSES and all(text), "invalid status or empty claim")
        heads[claim_id] = status
    return heads, history


def validate(document, edition, previous, previous_edition, resolve):
    current_version, old_version = version(edition), version(previous_edition)
    require(current_version >= old_version, "publication edition regressed")
    heads, history = parse(document)
    initial = hashlib.sha256(previous.encode()).hexdigest() == INITIAL_DOCUMENT_SHA256
    if initial:
        require(previous_edition == "3.3.0", "initial ledger edition mismatch")
        old_heads = {f"C{i:02d}": state for i, state in enumerate(INITIAL_STATUS, 1)}
        require(len(history) >= len(old_heads), "initial claim history missing")
        for i, entry in enumerate(history[:len(old_heads)], 1):
            require(entry[:3] == (f"C{i:02d}", "3.3.0", INITIAL_STATUS[i-1]), "initial assessment changed")
        prefix_length = len(old_heads)
    else:
        old_heads, old_history = parse(previous)
        require(history[:len(old_history)] == old_history, "previous history prefix changed or removed")
        prefix_length = len(old_history)
    require(set(old_heads) <= set(heads), "claim disappeared; retain it with an explicit status")
    last, seen, preceding = {}, set(), (0, 0, 0)
    for position, (claim_id, event_edition, status, reason, evidence) in enumerate(history):
        event_version = version(event_edition)
        require(claim_id in heads and status in STATUSES and bool(reason), "invalid history entry")
        require((claim_id, event_edition) not in seen, "two status entries for one claim in the same edition")
        require(preceding <= event_version <= current_version, "history edition order mismatch")
        if position >= prefix_length:
            require(event_version == current_version and current_version > old_version,
                    "a status entry requires a new publication edition")
        require(bool(re.fullmatch(r"[0-9a-f]{40}:[A-Za-z0-9_./-]+", evidence)), "evidence needs a full commit and path")
        commit, path = evidence.split(":", 1)
        require(not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts,
                "unsafe evidence path")
        require(resolve(commit, path), "evidence absent from its recorded commit")
        seen.add((claim_id, event_edition))
        preceding = event_version
        last[claim_id] = status
    require(heads == last, "current status does not match its history")
    return {"claims": len(heads), "entries": len(history), "prior_entries_preserved": prefix_length,
            "edition": edition, "semantic_support_verified": False}


def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False)
    require(result.returncode == 0, "required local Git source unavailable")
    return result.stdout


def main():
    document = (ROOT / "CLAIMS.md").read_text()
    metadata = (ROOT / "edition.json").read_text()
    edition = json.loads(metadata)["version"]
    # Uncommitted edits compare with HEAD; a committed edition compares with
    # its first parent, including a squash publication or a merged branch.
    committed = git("show", "HEAD:CLAIMS.md")
    committed_metadata = git("show", "HEAD:edition.json")
    revision = "HEAD" if document != committed or metadata != committed_metadata else "HEAD^"
    previous = git("show", f"{revision}:CLAIMS.md")
    previous_edition = json.loads(git("show", f"{revision}:edition.json"))["version"]

    def resolve(commit, path):
        result = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-t", f"{commit}:{path}"],
                                capture_output=True, text=True, check=False)
        return result.returncode == 0 and result.stdout.strip() == "blob"

    print(json.dumps(validate(document, edition, previous, previous_edition, resolve), sort_keys=True))


if __name__ == "__main__":
    main()
