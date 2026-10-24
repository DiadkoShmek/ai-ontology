#!/usr/bin/env python3
"""Verify selected saved DATA only. Archived programs remain inert strings.

Pins establish consistency with this selected packet, not historical origin,
provider identity, independent preregistration, or execution of archived source.
Saved reference labels are trusted authored outcomes; no mechanism is simulated.
"""
import base64
import gzip
import hashlib
import io
import json
import math
from fractions import Fraction
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
MAPPING_SHA256 = 'ed649c3034257ea77a4449df75cd14c11abf24925c591cb50e86f834ef691e5f'
PAYLOAD_SHA256 = '005eb56b86b8277a2cc53f8fced789dbae3895f6337232ba0f35cd3705802c2e'
SCHEMA = 'selected-forecast-calibration-projection/1'
SCHEDULE = (
    ('revision-01', 'u0', 'flat'), ('revision-02', 'u1', 'organized'),
    ('revision-03', 'u0', 'organized'), ('revision-04', 'u1', 'flat'),
    ('revision-05', 'u0', 'organized'), ('revision-06', 'u1', 'flat'),
    ('revision-07', 'u0', 'flat'), ('revision-08', 'u1', 'organized'))
SLOTS = ('m0',) + tuple(s[0] for s in SCHEDULE)
QUERIES = tuple('e%02d' % i for i in range(5, 17))
PROB = re.compile(r'(0|[1-9][0-9]{0,8})(?:/([1-9][0-9]{0,8}))?\Z', re.ASCII)
HEX = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def keys(value, names, reason='closed-schema'):
    require(type(value) is dict and set(value) == set(names), reason)


def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def equal(a, b, reason):
    require(same(a, b), reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def wire(value, ascii_only=False):
    return json.dumps(value, ensure_ascii=ascii_only,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def bounded(value, depth=0):
    require(depth <= 32, 'json-depth')
    if type(value) is dict:
        require(all(type(k) is str for k in value), 'json-key-type')
        for v in value.values():
            bounded(v, depth + 1)
    elif type(value) is list:
        for v in value:
            bounded(v, depth + 1)
    elif type(value) is float:
        require(math.isfinite(value), 'nonfinite-number')
    else:
        require(value is None or type(value) in (str, int, bool), 'json-type')


def strict(raw):
    def pairs(rows):
        out = {}
        for k, v in rows:
            require(k not in out, 'duplicate-json-key')
            out[k] = v
        return out
    def bad(_):
        raise ValueError('nonfinite-number')
    require(type(raw) is bytes and len(raw) <= 2097152, 'json-byte-cap')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=bad)
        bounded(value)
        return value
    except RecursionError as exc:
        raise ValueError('json-depth') from exc


def text(value, cap, reason):
    require(type(value) is str, reason + '-type')
    raw = value.encode('utf-8')
    require(len(raw) <= cap, reason + '-cap')
    return raw


def integer(value):
    return type(value) is int and value >= 0


def duration(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            'finite-nonnegative-duration')


def digest(value):
    require(type(value) is str and HEX.fullmatch(value), 'sha256-type')


def load_projection(projection_path=HERE / 'projection.json.gz',
                    mapping_path=HERE / 'projection-mapping.json'):
    with Path(projection_path).open('rb') as f:
        compressed = f.read(262145)
    require(len(compressed) <= 262144, 'compressed-cap')
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(2097153)
    require(len(raw) <= 2097152, 'decompressed-cap')
    with Path(mapping_path).open('rb') as f:
        mapping_raw = f.read(131073)
    require(len(mapping_raw) <= 131072, 'mapping-cap')
    document = strict(raw)
    keys(document, ('schema', 'mapping', 'payload'))
    external = strict(mapping_raw)
    equal(external, document['mapping'], 'external-mapping-equality')
    require(mapping_raw == canonical(external) + b'\n', 'external-mapping-canonical')
    require(sha(mapping_raw) == MAPPING_SHA256, 'external-mapping-pin')
    require(sha(canonical(document['payload'])) == PAYLOAD_SHA256, 'payload-pin')
    return document


def forecast(raw, labels):
    value = strict(raw)
    keys(value, ('distribution',), 'forecast-shape')
    require(type(value['distribution']) is dict, 'distribution-shape')
    probabilities = {label: Fraction(0) for label in labels}
    for label, token in value['distribution'].items():
        require(label in probabilities and type(token) is str and PROB.fullmatch(token),
                'forecast-label-or-token')
        probability = Fraction(token)
        require(0 <= probability <= 1, 'forecast-range')
        probabilities[label] = probability
    require(sum(probabilities.values(), Fraction()) == 1, 'forecast-mass')
    return value, probabilities


def expected_ledger(evidence, source_sha, historical):
    rows, available = [], []
    def add(row):
        rows.append({'seq': len(rows), **row})
    def episode(ep):
        eid = ep['id']
        add({'id': 'ep-' + eid, 'kind': 'episode', 'episode_id': eid})
        obs = {o['operation_id']: o['origin'] for o in ep['observations']}
        for op in ep['operations']:
            fields = {('cache_revision' if k == 'revision' else k): v
                      for k, v in op.items() if k != 'id'}
            add({'id': 'op-' + op['id'], 'kind': 'operation',
                 'episode_id': eid, 'operation_id': op['id'], **fields})
            if op['op'] == 'read':
                oid = 'ob-' + op['id']
                add({'id': oid, 'kind': 'observation', 'episode_id': eid,
                     'operation_id': op['id'], 'origin': obs[op['id']]})
                available.append(oid)
    for ep in evidence[:2]:
        episode(ep)
    add({'id': 'cm0', 'kind': 'commitment', 'episode_id': 'e03',
         'target_operation_id': 'e03-p05', 'policy_version': source_sha,
         'distribution': historical['distribution'],
         'available_observation_ids': list(available),
         'declared_used_observation_ids': [], 'authorship': 'participant'})
    for ep in evidence[2:]:
        episode(ep)
    return rows


def decode_view(raw, organized):
    if not organized:
        lines = raw.splitlines()
        require(bool(lines), 'flat-empty')
        equal(strict(lines[0]), {'schema': 'cache-evidence-flat/1'}, 'flat-header')
        return [strict(row) for row in lines[1:]]
    value = strict(raw)
    keys(value, ('schema', 'episodes', 'index'), 'organized-schema')
    equal(value['schema'], 'cache-evidence-organized/1', 'organized-schema-name')
    require(type(value['episodes']) is list, 'organized-episodes')
    rows = []
    for ep in value['episodes']:
        keys(ep, ('episode_id', 'records'), 'organized-episode')
        require(type(ep['records']) is list, 'organized-records')
        rows.extend(ep['records'])
    require(all(type(r) is dict and integer(r.get('seq')) for r in rows), 'ledger-seq')
    rows.sort(key=lambda r: r['seq'])
    episodes = list(dict.fromkeys(r['episode_id'] for r in rows))
    groups = [{'episode_id': eid, 'records': [r for r in rows if r['episode_id'] == eid]}
              for eid in episodes]
    refs = []
    for r in rows:
        if r['kind'] == 'observation':
            refs.append({k: r[v] for k, v in
                         (('record_id', 'id'), ('episode_id', 'episode_id'),
                          ('operation_id', 'operation_id'))})
        elif r['kind'] == 'commitment':
            refs.append({'record_id': r['id'], **{k: r[k] for k in
                ('episode_id', 'target_operation_id', 'policy_version',
                 'available_observation_ids', 'declared_used_observation_ids')}})
    equal(value['episodes'], groups, 'literal-groups')
    equal(value['index'], {'episode_records': [
        {'episode_id': eid, 'record_ids': [r['id'] for r in rows if r['episode_id'] == eid]}
        for eid in episodes], 'literal_references': refs}, 'literal-index')
    return rows


def framing(prompt, task, instruction, legend):
    prefix = task + b'\n\n' + instruction.encode() + b'\n\n' + legend + b'\nCOMMON_METADATA_JSON\n'
    require(prompt.startswith(prefix), 'revision-common-prefix')
    at = len(prefix)
    end = prompt.index(b'\n', at)
    metadata = strict(prompt[at:end])
    at = end + 1
    def block(at, marker):
        require(prompt[at:].startswith(marker), 'length-marker')
        at += len(marker)
        end = prompt.index(b'\n', at)
        token = prompt[at:end]
        require(bool(token) and len(token) <= 6 and token.isdigit()
                and str(int(token)).encode() == token, 'length-token')
        n = int(token)
        at = end + 1
        raw = prompt[at:at+n]
        require(len(raw) == n, 'length-short')
        return raw, at+n
    source, at = block(at, b'M0_SOURCE_UTF8_BYTES:')
    marker = b'\nEND_M0_SOURCE\n'
    require(prompt[at:at+len(marker)] == marker, 'source-end')
    view, at = block(at+len(marker), b'EVIDENCE_VIEW_UTF8_BYTES:')
    require(view.endswith(b'\n') and prompt[at:] == b'END_EVIDENCE_VIEW\n', 'view-end')
    return metadata, source, view


def verify(document):
    bounded(document)
    keys(document, ('schema', 'mapping', 'payload'))
    equal(document['schema'], SCHEMA, 'projection-schema')
    mapping, p = document['mapping'], document['payload']
    keys(mapping, ('schema', 'payload_sha256', 'selection', 'omissions', 'original_digests'))
    equal(mapping['schema'], 'selected-forecast-calibration-mapping/1', 'mapping-schema')
    for field in ('selection', 'omissions'):
        require(type(mapping[field]) is list and bool(mapping[field]), 'mapping-text-list')
        for item in mapping[field]:
            require(bool(text(item, 8192, 'mapping-text')), 'empty-mapping-text')
    digest(mapping['payload_sha256'])
    require(sha(canonical(p)) == mapping['payload_sha256'], 'embedded-payload-digest')
    # The fixed payload pin is intentionally checked by load_projection. Calling
    # verify directly lets adversarial tests rehash DATA and reach semantic checks.
    keys(p, ('task_utf8', 'initial_payload_utf8', 'cases_utf8', 'observed_utf8',
             'instructions', 'calls', 'captures', 'actual_origins', 'declared_summary'))
    originals = mapping['original_digests']
    keys(originals, ('task', 'cases', 'observed', 'reference', 'registration',
                     'schedule', 'calls', 'captures'))
    for name in ('task', 'cases', 'observed', 'reference', 'registration', 'schedule'):
        digest(originals[name])
    task = text(p['task_utf8'], 196608, 'task')
    require(sha(task) == originals['task'], 'original-task')
    cases_raw = text(p['cases_utf8'], 196608, 'cases')
    observed_raw = text(p['observed_utf8'], 196608, 'observed')
    require(sha(cases_raw) == originals['cases'], 'original-cases')
    require(sha(observed_raw) == originals['observed'], 'original-observed')
    cases_doc, observed = strict(cases_raw), strict(observed_raw)
    cases = {e['id']: e for e in cases_doc['episodes']}
    equal(list(cases), ['e%02d' % i for i in range(1, 17)], 'episode-order-coverage')
    require(len(cases_doc['episodes']) == 16, 'duplicate-episode')
    initial = strict(text(p['initial_payload_utf8'], 196608, 'initial-payload'))
    keys(initial, ('schema', 'evidence', 'diagnostic_query'))
    equal(initial['schema'], 'cache-initial-authoring/1', 'initial-schema')
    instructions = p['instructions']
    keys(instructions, ('initial', 'revision', 'legend'))
    for v in instructions.values():
        text(v, 196608, 'instruction')
    units = observed['units']
    equal([u['unit_id'] for u in units], ['u0', 'u1'], 'observed-unit-coverage')
    def evidence(unit, stage):
        u = next(x for x in units if x['unit_id'] == unit)
        stages = [s for s in u['stages'] if s['stage_id'] == stage]
        require(len(stages) == 1, 'evidence-stage-coverage')
        rows = stages[0]['evidence']
        equal([r['episode_id'] for r in rows], ['e01', 'e02'] +
              (['e03', 'e04'] if stage == 'E1' else []), 'evidence-episode-coverage')
        return [{'id': e['episode_id'], 'operations': cases[e['episode_id']]['operations'],
                 'observations': e['observations']} for e in rows]
    equal(initial['evidence'], evidence('u0', 'E0'), 'initial-evidence')
    equal(evidence('u0', 'E0'), evidence('u1', 'E0'), 'shared-E0')
    def query(eid):
        if eid == 'e03':
            q = initial['diagnostic_query']
            keys(q, ('id', 'operations', 'target_read', 'origin_labels'))
            equal(q['id'], eid, 'diagnostic-id')
            equal(q['operations'], cases[eid]['operations'], 'diagnostic-operations')
        else:
            e = cases[eid]
            q = {'id': eid, 'operations': e['operations'], 'target_read': e['target_read']}
        labels = []
        found = False
        for op in q['operations']:
            if op['id'] == q['target_read']:
                require(op['op'] == 'read', 'target-operation')
                found = True
                break
            if op['op'] == 'write':
                labels.append(op['origin'])
        require(found, 'missing-target')
        if eid == 'e03':
            equal(q['origin_labels'], sorted(labels), 'diagnostic-labels')
        else:
            q['origin_labels'] = sorted(labels)
        return q
    actual = p['actual_origins']
    keys(actual, ('u0', 'u1'))
    for u in ('u0', 'u1'):
        keys(actual[u], ('e03',) + QUERIES)
        target = query('e03')['target_read']
        selected = [o['origin'] for e in evidence(u, 'E1') if e['id'] == 'e03'
                    for o in e['observations'] if o['operation_id'] == target]
        equal(selected, [actual[u]['e03']], 'diagnostic-reference-observation')
        for q in ('e03',) + QUERIES:
            require(type(actual[u][q]) is str and actual[u][q] in query(q)['origin_labels'],
                    'saved-reference-origin')
    calls = p['calls']
    keys(calls, SLOTS, 'call-coverage')
    keys(originals['calls'], SLOTS, 'call-original-coverage')
    carriers, prompts, timings = {}, {}, {}
    for slot in SLOTS:
        c = calls[slot]
        keys(c, ('prompt_utf8', 'response_utf8', 'prompt_sha256', 'response_sha256',
                 'source_sha256', 'method_note_sha256', 'usage', 'observer_elapsed_s', 'terminal'))
        prompt = text(c['prompt_utf8'], 196608, 'prompt')
        response = text(c['response_utf8'], 32768, 'response')
        carrier = strict(response)
        keys(carrier, ('source', 'method_note'), 'carrier-schema')
        source = text(carrier['source'], 24576, 'source')
        note = text(carrier['method_note'], 1024, 'method-note')
        for name, raw in (('prompt', prompt), ('response', response), ('source', source), ('method_note', note)):
            equal(c[name + '_sha256'], sha(raw), 'call-' + name + '-binding')
        origin = originals['calls'][slot]
        keys(origin, ('prompt', 'response_container', 'native_observer'))
        for h in origin.values():
            digest(h)
        equal(origin['prompt'], sha(prompt), 'original-prompt')
        keys(c['usage'], ('input_tokens', 'output_tokens', 'cached_input_tokens'))
        require(all(integer(n) for n in c['usage'].values()), 'usage-integer')
        require(c['usage']['cached_input_tokens'] <= c['usage']['input_tokens'], 'usage-cache-subset')
        equal(c['terminal'], {'exit_code': 0, 'owned_leader_reaped': True,
                             'streams_complete': True, 'group_closure': 'unknown'}, 'selected-terminal')
        duration(c['observer_elapsed_s'])
        carriers[slot], prompts[slot], timings[slot] = carrier, prompt, c['observer_elapsed_s']
    expected_initial = task + b'\n\n' + instructions['initial'].encode() + b'\n\nINPUT_JSON\n' + wire(initial) + b'\n'
    equal(prompts['m0'], expected_initial, 'initial-prompt-reconstruction')
    plan = [('diagnostic', 'm0', None, 'E0', 'e03')]
    plan += [('eval-m0-E0-' + q, 'm0', None, 'E0', q) for q in QUERIES]
    plan += [('eval-m0-' + u + '-E1-' + q, 'm0', u, 'E1', q)
             for u in ('u0', 'u1') for q in QUERIES]
    plan += [('eval-' + s + '-' + q, s, u, 'E1', q) for s, u, _ in SCHEDULE for q in QUERIES]
    require(type(p['captures']) is list and len(p['captures']) == 133, 'capture-count')
    keys(originals['captures'], [r[0] for r in plan], 'original-capture-coverage')
    distributions, losses, diagnostic = {}, {}, None
    truth_count = 0
    for capture, (cid, slot, unit, stage, qid) in zip(p['captures'], plan):
        keys(capture, ('id', 'source_slot', 'unit', 'evidence', 'query', 'source_sha256',
            'request_sha256', 'request_utf8', 'stdout_utf8', 'stdout_sha256', 'stderr_utf8',
            'stderr_sha256', 'outer_returncode', 'source_error', 'observer_error',
            'requested_stop', 'signal_sent', 'kill_method', 'checkpoint_count',
            'artifact_count', 'elapsed_s', 'score_declarations'))
        equal([capture[k] for k in ('id', 'source_slot', 'unit', 'evidence', 'query')],
              [cid, slot, unit, stage, qid], 'capture-order-descriptor')
        equal(capture['source_sha256'], calls[slot]['source_sha256'], 'capture-source')
        expected = {'schema': 'cache-forecast-request/1',
                    'evidence': initial['evidence'] if qid == 'e03' else evidence(unit or 'u0', stage),
                    'query': query(qid)}
        request = text(capture['request_utf8'], 262144, 'request')
        equal(request, wire(expected, ascii_only=True), 'canonical-request-wire')
        stdout = text(capture['stdout_utf8'], 65536, 'stdout')
        stderr = text(capture['stderr_utf8'], 65536, 'stderr')
        require(len(stdout) + len(stderr) <= 65536, 'combined-stream-cap')
        for name, raw in (('request', request), ('stdout', stdout), ('stderr', stderr)):
            equal(capture[name + '_sha256'], sha(raw), 'capture-' + name + '-hash')
        origin = originals['captures'][cid]
        keys(origin, ('source', 'request', 'stdout', 'stderr', 'source_result', 'result'))
        for h in origin.values():
            digest(h)
        for name in ('source', 'request', 'stdout', 'stderr'):
            equal(origin[name], capture[name + '_sha256'], 'original-capture-' + name)
        for field in ('outer_returncode', 'checkpoint_count', 'artifact_count'):
            equal(capture[field], 0, 'capture-clean-' + field)
        for field in ('source_error', 'observer_error', 'requested_stop', 'signal_sent', 'kill_method'):
            equal(capture[field], None, 'capture-clean-' + field)
        duration(capture['elapsed_s'])
        raw_forecast, probs = forecast(stdout, expected['query']['origin_labels'])
        score_units = ('u0', 'u1') if unit is None else (unit,)
        keys(capture['score_declarations'], score_units, 'score-unit-coverage')
        for u in score_units:
            loss = 1 + sum(v*v for v in probs.values()) - 2*probs[actual[u][qid]]
            equal(capture['score_declarations'][u],
                  {'status': 'valid', 'valid_brier': str(loss), 'composite_loss': str(loss)},
                  'saved-score-algebra')
            distributions[(u, slot, stage, qid)] = probs
            losses[(u, slot, stage, qid)] = loss
            truth_count += 1
        if cid == 'diagnostic':
            diagnostic = (capture, raw_forecast)
    require(truth_count == 146, 'truth-row-count')
    dc, historical = diagnostic
    capsule = {'source_sha256': calls['m0']['source_sha256'],
               'request_sha256': dc['request_sha256'], 'status': 'valid',
               'stdout_base64': base64.b64encode(dc['stdout_utf8'].encode()).decode(),
               'stderr_base64': base64.b64encode(dc['stderr_utf8'].encode()).decode(),
               'strict_forecast_or_null': historical, 'parser_reason_or_null': None}
    repeats = {}
    for slot, u, fmt in SCHEDULE:
        metadata, source, view = framing(prompts[slot], task, instructions['revision'], instructions['legend'].encode())
        equal(source, carriers['m0']['source'].encode(), 'historical-source-verbatim')
        equal(metadata, {'schema': 'cache-revision-authoring/1',
                         'm0_source_sha256': calls['m0']['source_sha256'],
                         'm0_method_note': carriers['m0']['method_note'],
                         'diagnostic_capture': capsule}, 'common-metadata-capsule')
        equal(decode_view(view, fmt == 'organized'),
              expected_ledger(evidence(u, 'E1'), calls['m0']['source_sha256'], historical),
              'same-information-ledger')
        if (u, fmt) in repeats:
            equal(prompts[slot], repeats[(u, fmt)], 'repeat-identical-prompt')
        repeats[(u, fmt)] = prompts[slot]
    def mean(values):
        require(bool(values), 'empty-mean')
        return sum(values, Fraction()) / len(values)
    def source_mean(u, slot, stage, queries):
        return mean([losses[(u, slot, stage, q)] for q in queries])
    transfer, retention, ranges, contrasts, controls = {}, {}, {}, {}, {}
    for u in ('u0', 'u1'):
        formats = {}
        for fmt in ('flat', 'organized'):
            values = []
            for slot, world, form in SCHEDULE:
                if (world, form) != (u, fmt):
                    continue
                value = source_mean(u, slot, 'E1', QUERIES[:8])
                transfer[u + ':' + slot] = str(value)
                retention[u + ':' + slot] = str(source_mean(u, slot, 'E1', QUERIES[8:]))
                values.append(value)
            require(len(values) == 2, 'two-repeats-per-world-format')
            ranges[u + ':' + fmt] = str(abs(values[0] - values[1]))
            formats[fmt] = mean(values)
        contrasts[u] = str(formats['flat'] - formats['organized'])
        for stage in ('E0', 'E1'):
            for role, qs in (('transfer', QUERIES[:8]), ('retention', QUERIES[8:])):
                controls[':'.join((u, stage, role))] = str(source_mean(u, 'm0', stage, qs))
    usage = {'model_callbacks': 9, 'main_unknown_calls': 0,
             'known_input_sum': sum(c['usage']['input_tokens'] for c in calls.values()),
             'known_output_sum': sum(c['usage']['output_tokens'] for c in calls.values()),
             'known_cached_sum': sum(c['usage']['cached_input_tokens'] for c in calls.values()),
             'cached_unknown_calls': 0, 'reported_main_totals_complete': True,
             'reported_only_not_billing_attestation': True}
    changed = sum(distributions[(u, s, 'E1', q)] != distributions[(u, 'm0', 'E1', q)]
                  for s, u, _ in SCHEDULE for q in QUERIES)
    regressions = sum(losses[(u, s, 'E1', q)] > losses[(u, 'm0', 'E1', q)]
                      for s, u, _ in SCHEDULE for q in QUERIES[8:])
    costs = {}
    for fmt in ('flat', 'organized'):
        slots = [s for s, _, form in SCHEDULE if form == fmt]
        costs[fmt] = {'prompt_bytes': sum(len(prompts[s]) for s in slots),
            'source_bytes': sum(len(carriers[s]['source'].encode()) for s in slots),
            **{k: sum(calls[s]['usage'][k] for s in slots)
               for k in ('input_tokens', 'output_tokens', 'cached_input_tokens')},
            'native_observer_seconds': sum(timings[s] for s in slots), 'model_calls': 4}
    result = {'D_by_world': contrasts,
              'D_overall': str(mean([Fraction(v) for v in contrasts.values()])),
              'transfer_source_means': transfer, 'within_format_ranges': ranges,
              'retention_source_means': retention, 'M0_control_means': controls,
              'model_usage': usage, 'changed_distribution_count': changed,
              'retention_regression_count': regressions, 'format_costs': costs}
    declared = p['declared_summary']
    keys(declared, result.keys(), 'summary-schema')
    for key in result:
        if key != 'format_costs':
            equal(declared[key], result[key], 'summary-' + key)
    keys(declared['format_costs'], ('flat', 'organized'))
    for fmt in costs:
        keys(declared['format_costs'][fmt], costs[fmt].keys())
        for key, expected in costs[fmt].items():
            value = declared['format_costs'][fmt][key]
            if key == 'native_observer_seconds':
                duration(value)
                require(abs(value - expected) <= 1e-9, 'format-duration-sum')
            else:
                equal(value, expected, 'format-cost-' + key)
    return {'status': 'consistent-selected-saved-data', 'model_calls': 9,
            'source_captures': 133, 'truth_rows': truth_count,
            'source_byte_changed_count': sum(calls[s]['source_sha256'] != calls['m0']['source_sha256']
                                             for s, _, _ in SCHEDULE), **result,
            'scope': 'Saved DATA consistency only; no source rerun or origin authentication.'}


def main():
    print(json.dumps(verify(load_projection()), ensure_ascii=False,
                     separators=(',', ':'), allow_nan=False))


if __name__ == '__main__':
    main()
