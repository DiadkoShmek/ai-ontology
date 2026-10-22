"""Explicit local qualification run; no downloads, retries or provider fallback."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
import urllib.request

from design import ARMS, SYSTEM, SCHEMA, make_cases, prompt, score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODELS = ('qwen3:4b-instruct-2507-q4_K_M', 'granite3.3:2b')
OPTIONS = {'temperature': 0, 'seed': 941, 'num_ctx': 8192,
           'num_predict': 384, 'num_thread': 2}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def call(path, body=None, timeout=60):
    req = urllib.request.Request('http://127.0.0.1:11434' + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read(4*1024*1024+1)
    if len(raw) > 4*1024*1024:
        raise ValueError('backend-response-limit')
    return json.loads(raw)


def model_pins():
    tags = {m['name']: m for m in call('/api/tags')['models']}
    pins = []
    for name in MODELS:
        model = tags[name]
        detail = call('/api/show', {'model': name})
        pins.append({'name': name, 'digest': model['digest'], 'size': model['size'],
            'details': model.get('details'),
            'template_sha256': sha(detail.get('template', '').encode()),
            'parameters_sha256': sha('\n'.join(sorted(detail.get('parameters', '').splitlines())).encode())})
    return pins


def source_pins():
    names = ['design.py', 'run.py', 'analyze.py', 'test_design.py',
             'PROTOCOL.md', 'METHOD_UA.md', 'cases.json']
    return {name: sha((HERE / name).read_bytes()) for name in names}


def request_messages(case, arm, stage_index, previous, method):
    messages = [{'role': 'system', 'content': SYSTEM}]
    if case['family'] == 'history_loss' and stage_index:
        # The source profile and earlier task prompt are actually unavailable.
        # Preserve the real earlier visible reply as an unbound handoff record.
        messages.append({'role': 'user', 'content': json.dumps({
            'handoff': previous[-1], 'binding': 'profile record unavailable'}, sort_keys=True)})
    else:
        for i, row in enumerate(previous):
            messages.append(prompt(case['stages'][i], arm, method))
            if row.get('response'):
                messages.append({'role': 'assistant', 'content': row['response']})
            messages.append({'role': 'user', 'content': json.dumps({
                'observed_adapter_effect': row['effect']}, sort_keys=True)})
    messages.append(prompt(case['stages'][stage_index], arm, method))
    return messages


def apply_choice(folder, case, stage_index, evaluated, terminal):
    choice = evaluated['choice']
    if not terminal or not evaluated['shape']:
        return {'plan_written': False, 'reason': 'invalid-or-incomplete'}
    if choice == 'ASK':
        return {'plan_written': False, 'reason': 'deferred'}
    action = case['stages'][stage_index]['actions'][choice]
    if not action['available']:
        return {'plan_written': False, 'reason': 'unavailable-choice-refused'}
    body = {'case': case['id'], 'stage': stage_index, 'choice': choice,
            'action': action}
    raw = json.dumps(body, sort_keys=True).encode()
    target = folder / ('plan-' + str(stage_index) + '.json')
    with target.open('xb') as output:
        output.write(raw)
    observed = target.read_bytes()
    if observed != raw:
        raise ValueError('plan-readback-mismatch')
    return {'plan_written': True, 'sha256': sha(observed), 'body': body}


def freeze():
    target = HERE / 'freeze.json'
    if target.exists() or (HERE / 'cases.json').exists():
        raise ValueError('already-prepared')
    (HERE / 'cases.json').write_text(json.dumps(make_cases(), indent=2) + '\n')
    value = {'schema': 'participation-pilot-freeze/1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'input_sha256': source_pins(), 'models': model_pins(),
        'backend': call('/api/version'), 'options': OPTIONS,
        'arms': list(ARMS), 'scored_calls': 136, 'warmups': 2,
        'schedule_seed': 941, 'independent_registration': False}
    target.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'frozen': 136, 'sha256': sha(target.read_bytes())}))


def run():
    frozen = json.loads((HERE / 'freeze.json').read_text())
    if frozen['input_sha256'] != source_pins() or frozen['models'] != model_pins():
        raise ValueError('frozen-source-or-model-drift')
    paths = [str((HERE / n).relative_to(ROOT)) for n in frozen['input_sha256']] + [str((HERE / 'freeze.json').relative_to(ROOT))]
    if subprocess.check_output(['git', 'status', '--porcelain', '--', *paths], cwd=ROOT):
        raise ValueError('inputs-not-committed')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    cases = json.loads((HERE / 'cases.json').read_text())
    method = (HERE / 'METHOD_UA.md').read_text()
    before = call('/api/ps')['models']
    count = 0
    began = time.perf_counter()
    target = HERE / 'responses.jsonl'
    with target.open('x') as output:
        for model in MODELS:
            try:
                warm = call('/api/chat', {'model': model, 'messages': [{'role': 'user', 'content': 'Return JSON {"ready":true}'}],
                    'format': 'json', 'stream': False, 'options': OPTIONS, 'keep_alive': '2m'}, timeout=90)
                (HERE / ('warmup-' + str(MODELS.index(model)) + '.json')).write_text(json.dumps({
                    k: v for k, v in warm.items() if k != 'message'}, indent=2) + '\n')
                schedule = [(case, arm) for case in cases for arm in ARMS]
                random.Random(941).shuffle(schedule)
                for case, arm in schedule:
                    previous = []
                    with tempfile.TemporaryDirectory() as folder:
                        for index, expected in enumerate(case['expected_choices']):
                            messages = request_messages(case, arm, index, previous, method)
                            payload = {'model': model, 'messages': messages, 'format': SCHEMA,
                                       'stream': False, 'options': OPTIONS, 'keep_alive': '2m'}
                            row = {'model': model, 'case': case['id'], 'family': case['family'],
                                   'profile': case['profile'], 'arm': arm, 'stage': index,
                                   'input_commit': commit, 'messages': messages,
                                   'request_sha256': sha(json.dumps(payload, sort_keys=True).encode())}
                            started = time.perf_counter()
                            try:
                                reply = call('/api/chat', payload)
                                content = reply.get('message', {}).get('content', '')
                                terminal = reply.get('done') is True and reply.get('done_reason') == 'stop' and reply.get('model') == model
                                evaluated = score(content, expected)
                                row.update(response=content, terminal=terminal, score=evaluated,
                                    backend={k: reply.get(k) for k in ('model', 'done', 'done_reason', 'prompt_eval_count',
                                              'eval_count', 'total_duration', 'load_duration')})
                                row['score']['correct'] = bool(evaluated['correct'] and terminal)
                                row['effect'] = apply_choice(Path(folder), case, index, evaluated, terminal)
                            except Exception as error:
                                row.update(error=type(error).__name__, terminal=False,
                                    score={'shape': False, 'choice': None, 'correct': False},
                                    effect={'plan_written': False, 'reason': 'request-or-adapter-error'})
                            row['wall_ms'] = round((time.perf_counter()-started)*1000, 3)
                            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
                            output.flush()
                            previous.append({'response': row.get('response'), 'effect': row['effect']})
                            count += 1
                            if count % 8 == 0:
                                print(json.dumps({'completed': count, 'total': 136, 'elapsed_s': round(time.perf_counter()-began, 1)}), flush=True)
            finally:
                call('/api/generate', {'model': model, 'keep_alive': 0})
    after = call('/api/ps')['models']
    unchanged = model_pins() == frozen['models']
    if count != 136 or not unchanged:
        raise ValueError('completion-or-model-drift')
    completion = {'input_commit': commit, 'scored_calls': count,
        'response_sha256': sha(target.read_bytes()), 'freeze_sha256': sha((HERE/'freeze.json').read_bytes()),
        'wall_seconds': time.perf_counter()-began, 'models_unchanged': unchanged,
        'resident_models_before': before, 'resident_models_after': after,
        'completed_at': datetime.now(timezone.utc).isoformat()}
    (HERE / 'completion.json').write_text(json.dumps(completion, indent=2)+'\n')
    print(json.dumps({'completed': count, 'models_unchanged': unchanged}), flush=True)


if __name__ == '__main__':
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
