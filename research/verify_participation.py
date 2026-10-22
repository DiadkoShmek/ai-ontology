"""Offline reconstruction of the participation pilot; no model or network calls."""
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'research/participation_pilot'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    frozen = json.loads((HERE/'freeze.json').read_text())
    for name, pin in frozen['input_sha256'].items():
        require(hashlib.sha256((HERE/name).read_bytes()).hexdigest() == pin,
                'frozen source mismatch: '+name)
    sys.path.insert(0, str(HERE))
    from design import ARMS, SCHEMA, make_cases, oracle, score
    from run import OPTIONS, apply_choice, request_messages
    from analyze import derive
    require(frozen['options'] == OPTIONS and frozen['arms'] == list(ARMS), 'frozen execution settings mismatch')
    cases = json.loads((HERE/'cases.json').read_text())
    require(cases == make_cases(), 'case derivation mismatch')
    require(all(c['expected_choices'] == [oracle(s) for s in c['stages']] for c in cases), 'oracle mismatch')
    archive = HERE/'responses.jsonl.gz'
    plain = HERE/'responses.jsonl'
    raw = gzip.decompress(archive.read_bytes()) if archive.exists() else plain.read_bytes()
    if archive.exists() and plain.exists():
        require(raw == plain.read_bytes(), 'archive/raw mismatch')
    completion = json.loads((HERE/'completion.json').read_text())
    require(hashlib.sha256(raw).hexdigest() == completion['response_sha256'], 'response hash mismatch')
    require(hashlib.sha256((HERE/'freeze.json').read_bytes()).hexdigest() == completion['freeze_sha256'], 'freeze mismatch')
    rows = [json.loads(line) for line in raw.splitlines()]
    require(len(rows) == completion['scored_calls'] == frozen['scored_calls'] == 136, 'coverage mismatch')
    method = (HERE/'METHOD_UA.md').read_text()
    cursor = 0
    for model in frozen['models']:
        schedule = [(case, arm) for case in cases for arm in ARMS]
        random.Random(frozen['schedule_seed']).shuffle(schedule)
        for case, arm in schedule:
            previous = []
            with tempfile.TemporaryDirectory() as folder:
                for index, expected in enumerate(case['expected_choices']):
                    row = rows[cursor];cursor += 1
                    require((row['model'], row['case'], row['arm'], row['stage']) ==
                            (model['name'], case['id'], arm, index), 'schedule mismatch')
                    require(row['family'] == case['family'] and row['profile'] == case['profile'], 'case metadata mismatch')
                    require(row['input_commit'] == completion['input_commit'], 'input commit mismatch')
                    messages = request_messages(case, arm, index, previous, method)
                    require(row['messages'] == messages, 'request history mismatch')
                    payload = {'model': model['name'], 'messages': messages, 'format': SCHEMA,
                               'stream': False, 'options': OPTIONS, 'keep_alive': '2m'}
                    require(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest() == row['request_sha256'], 'request hash mismatch')
                    evaluated = score(row.get('response', ''), expected)
                    evaluated['correct'] = bool(evaluated['correct'] and row['terminal'])
                    require(evaluated == row['score'], 'score mismatch')
                    if 'error' not in row:
                        effect = apply_choice(Path(folder), case, index, evaluated, row['terminal'])
                        require(effect == row['effect'], 'artifact effect mismatch')
                    else:
                        require(not row['terminal'] and not row['effect']['plan_written'], 'invalid error outcome')
                    if row['terminal']:
                        require(row['backend']['model'] == model['name'] and row['backend']['done'] is True
                                and row['backend']['done_reason'] == 'stop', 'terminal metadata mismatch')
                    previous.append({'response': row.get('response'), 'effect': row['effect']})
    report = json.loads((HERE/'results.json').read_text())
    require(derive() == report, 'analysis drift')
    print(json.dumps({'calls': cursor, 'internally_consistent': True,
                      'scope': 'Published bytes, request history, scores and fixture effects; not independent replication.'}))


if __name__ == '__main__':
    main()
