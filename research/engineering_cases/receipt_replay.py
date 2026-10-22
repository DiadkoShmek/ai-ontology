"""Replay two historical engineering failures on isolated SQLite and files.

The three drain implementations and their readback helper are exact source
excerpts. This adapter supplies one artificial actor, event and append path;
it omits deployment policy and injects declared exceptions around real commits.
This is a retrospective component comparison, not a trial of natural faults,
model behavior or the causal effect of reading an ontology.
"""
import json
import argparse
import hashlib
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import before
import intermediate
import after
import common

ACTOR = 'agent-a'
EVENT = {'id': '00000000-0000-4000-8000-000000000001', 'kind': 'seen',
         'payload': {'throughSeq': 0}}


class FixtureJournal:
    recorded_event = common.recorded_event

    def __init__(self, root, fault):
        self.runtime = root
        self.fault = fault
        self.append_calls = 0
        self.read_calls = 0
        with closing(sqlite3.connect(root / 'journal.sqlite')) as db, db:
            db.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY, id TEXT UNIQUE, '
                       'actor TEXT, kind TEXT, payload TEXT, digest TEXT)')

    def append(self, actor, event):
        self.append_calls += 1
        if self.fault == 'precommit':
            raise OSError('injected before commit')
        payload = common.wire(event['payload'])
        pin = common.digest(common.wire({'actor': actor, 'kind': event['kind'],
                                        'payload': event['payload']}).encode())
        with closing(sqlite3.connect(self.runtime / 'journal.sqlite')) as db, db:
            row = db.execute('INSERT INTO events(id,actor,kind,payload,digest) VALUES(?,?,?,?,?)',
                             (event['id'], actor, event['kind'], payload, pin))
            seq = row.lastrowid
        if self.fault == 'postcommit':
            raise OSError('injected after commit')
        return {'id': event['id'], 'seq': seq, 'replayed': False}

    def count(self):
        with closing(sqlite3.connect(self.runtime / 'journal.sqlite')) as db:
            return db.execute('SELECT count(*) FROM events').fetchone()[0]

    def close(self):
        for scan in getattr(self, '_scans', {}).values():
            scan.close()


def replay(module, fault, interrupted_read=False):
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        inbox = root / 'shared-memory-inbox'
        inbox.mkdir()
        source = inbox / (EVENT['id'] + '.json')
        source.write_text(common.wire(EVENT))
        side = source.with_suffix('.receipt.json')
        journal = FixtureJournal(root, fault)
        try:
            module.drain(journal, {ACTOR: root})
            first = json.loads(side.read_text())
            if interrupted_read:
                read = module.read_file

                def failing_input(path, cap):
                    if Path(path) == source:
                        raise OSError('injected transient input read failure')
                    return read(path, cap)

                with patch.object(module, 'read_file', failing_input):
                    module.drain(journal, {ACTOR: root})
                journal.fault = None
            for _ in range(4):
                module.drain(journal, {ACTOR: root})
            return {'first_status': first['status'],
                    'last_status': json.loads(side.read_text())['status'],
                    'events': journal.count(), 'append_calls': journal.append_calls}
        finally:
            journal.close()


def run_cases():
    return {
        'commit_before_receipt_error': {
            'before': replay(before, 'postcommit'),
            'after': replay(after, 'postcommit')},
        'uncertainty_survives_input_read_failure': {
            'intermediate': replay(intermediate, 'precommit', True),
            'after': replay(after, 'precommit', True)},
        'scope': 'Retrospective source-excerpt replay; injected faults around real '
                 'temporary SQLite/file effects. No LLM or deployment execution.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = run_cases()
    if args.report:
        root = Path(__file__).resolve().parents[2]
        sources = sorted(Path(__file__).parent.glob('*.py')) + [Path(__file__).with_name('provenance.json')]
        result = {'schema': 'ontology-engineering-cases/1', 'cases': result,
                  'llm_calls': 0, 'historical_failures_reproduced': 2,
                  'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sources}}
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
