"""Verify a selected saved-evidence projection; never execute archived source.

Independent geometry/Brier/reference work is carried from the separately
authored local result auditor (source SHA b98c48de70e6b558c315ddf554f92ba1f639d2bec84dc46f58d215c0df3ef8c1)
and component DSU analysis (source SHA 928c26f1266164367f924db8f11f12390bd2cb214344cd04eda1945c697729ea).
No private modules, candidate modules or original scorer are imported here.
"""
from collections import deque
from fractions import Fraction
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zlib

HERE = Path(__file__).resolve().parent
MAPPING_SHA256 = 'de7f4722abfa3f22483386ab589d5cc1d4a2510f320bc594f77b7528b2087ccf'
PAYLOAD_SHA256 = '40d4cbf6807262de32ae8c1ac1acc0f400fe97790971f63a713c4f29a39a3c34'
MAX_COMPRESSED_BYTES = 131072
MAX_JSON_BYTES = 524288
MAX_MAPPING_BYTES = 131072
SLOTS = ('canary', 'm0', 'actual-free-a', 'actual-linked-a', 'actual-linked-b',
         'actual-free-b', 'masked-linked', 'masked-free', 'fresh-b', 'fresh-a')
WORLDS = ('w-a', 'w-b')
PAYLOAD_KEYS = {'calls', 'captures', 'cases_utf8', 'declared_conditions', 'declared_costs', 'declared_primary', 'prompt_constants'}
CALL_KEYS = {'event_types', 'exit_code', 'method_record_sha256', 'outer_wall_s', 'prompt', 'prompt_sha256', 'response', 'response_sha256', 'source_sha256', 'terminal', 'tools', 'usage', 'wall_ms'}
CAPTURE_KEYS = {'artifact_bytes', 'artifact_sha256', 'candidate_error', 'observer_error', 'outer_bwrap_returncode', 'record', 'request_sha256', 'request_utf8', 'slot', 'source_error', 'source_sha256', 'stderr_sha256', 'stderr_utf8', 'stdout_sha256', 'stdout_utf8'}


class ProjectionError(ValueError):
    """Invalid, incomplete, changed or overbound selected evidence."""


def require(condition, reason):
    if not condition:
        raise ProjectionError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def text_bytes(value, bound, label):
    require(type(value) is str, label + ': expected string')
    try:
        raw = value.encode('utf-8', 'strict')
    except UnicodeError as error:
        raise ProjectionError(label + ': invalid UTF8') from error
    require(len(raw) <= bound, label + ': byte cap')
    return raw


def exact_keys(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), label + ': exact keys')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def strict_json(raw, bound=MAX_JSON_BYTES):
    if type(raw) is str:
        raw = text_bytes(raw, bound, 'JSON')
    require(type(raw) is bytes and len(raw) <= bound, 'JSON byte cap')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ProjectionError('nonfinite JSON constant: ' + value)
    try:
        result = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=constant)
        pending = [(result, 0)]
        while pending:
            value, depth = pending.pop()
            require(depth <= 32, 'JSON depth cap')
            if type(value) is float:
                require(math.isfinite(value), 'nonfinite JSON number')
            elif type(value) is str:
                text_bytes(value, bound, 'JSON string')
            elif type(value) is dict:
                for key in value:
                    text_bytes(key, bound, 'JSON key')
                pending.extend((item, depth + 1) for item in value.values())
            elif type(value) is list:
                pending.extend((item, depth + 1) for item in value)
        return result
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ProjectionError('invalid bounded JSON') from error


def bounded_read(path, bound):
    with Path(path).open('rb') as stream:
        raw = stream.read(bound + 1)
    require(len(raw) <= bound, 'file byte cap: ' + Path(path).name)
    return raw


def load_projection(projection_path=HERE / 'projection.json.gz', mapping_path=HERE / 'projection-mapping.json'):
    mapping_raw = bounded_read(mapping_path, MAX_MAPPING_BYTES)
    require(sha(mapping_raw) == MAPPING_SHA256, 'external mapping pin')
    mapping = strict_json(mapping_raw, MAX_MAPPING_BYTES)
    compressed = bounded_read(projection_path, MAX_COMPRESSED_BYTES)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
    except (OSError, EOFError, zlib.error) as error:
        raise ProjectionError('invalid gzip projection') from error
    document = strict_json(raw)
    exact_keys(document, {'schema', 'mapping', 'payload'}, 'projection envelope')
    require(document['schema'] == 'selected-induction-projection/1', 'projection schema')
    require(document['mapping'] == mapping and sha(canonical(document['mapping']) + b'\n') == MAPPING_SHA256, 'embedded mapping pin')
    require(sha(canonical(document['payload'])) == PAYLOAD_SHA256 and mapping['payload_sha256'] == PAYLOAD_SHA256, 'payload pin')
    return document


def grid_key(grid, shape=None):
    require(type(grid) is list and 1 <= len(grid) <= 12, 'grid height')
    require(type(grid[0]) is list and 1 <= len(grid[0]) <= 12, 'grid width')
    size = (len(grid), len(grid[0]))
    require(shape is None or shape == size, 'grid shape')
    require(all(type(row) is list and len(row) == size[1] and all(type(value) is int and 0 <= value <= 4 for value in row) for row in grid), 'grid values')
    return tuple(tuple(row) for row in grid)


def parse_forecast(value, shape):
    exact_keys(value, {'hypotheses'}, 'forecast')
    require(type(value['hypotheses']) is list and len(value['hypotheses']) <= 3, 'hypothesis count')
    result = {}
    for hypothesis in value['hypotheses']:
        exact_keys(hypothesis, {'grid', 'probability'}, 'hypothesis')
        key = grid_key(hypothesis['grid'], shape)
        text = hypothesis['probability']
        require(type(text) is str and len(text) <= 64 and re.fullmatch(r'(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?', text) is not None, 'rational probability grammar')
        probability = Fraction(text)
        require(0 <= probability <= 1 and key not in result, 'probability range or duplicate grid')
        result[key] = probability
    require(sum(result.values(), Fraction()) <= 1, 'probability sum')
    return result


def distribution_equal(left, right, shape):
    """Compare every categorical probability, including the unlisted complement."""
    a, b = parse_forecast(left, shape), parse_forecast(right, shape)
    count = 5 ** (shape[0] * shape[1])
    qa = (1 - sum(a.values(), Fraction())) / (count - len(a))
    qb = (1 - sum(b.values(), Fraction())) / (count - len(b))
    union = set(a) | set(b)
    if count > len(union) and qa != qb:
        return False
    return all(a.get(key, qa) == b.get(key, qb) for key in union)


def brier(forecast, actual):
    key = grid_key(actual)
    probabilities = parse_forecast(forecast, (len(key), len(key[0])))
    residual = 1 - sum(probabilities.values(), Fraction())
    uniform = residual / (5 ** (len(key) * len(key[0])) - len(probabilities))
    return 1 + sum((p * p for p in probabilities.values()), Fraction()) + residual * uniform - 2 * probabilities.get(key, uniform)


def truth(grid, world):
    key = grid_key(grid)
    height, width = len(key), len(key[0])
    out = [list(row) for row in key]
    cells = [(r, c) for r in range(height) for c in range(width) if key[r][c]]
    if not cells:
        return out
    colors = {key[r][c] for r, c in cells}
    require(len(colors) == 1, 'reference truth is scoped to monochrome inputs')
    color = next(iter(colors))
    if world == 'w-b':
        for r in range(min(r for r, c in cells), max(r for r, c in cells) + 1):
            for c in range(min(c for r, c in cells), max(c for r, c in cells) + 1):
                out[r][c] = color
    else:
        require(world == 'w-a', 'reference world')
        exterior = set()
        queue = deque((r, c) for r in range(height) for c in range(width) if key[r][c] == 0 and (r in (0, height - 1) or c in (0, width - 1)))
        while queue:
            r, c = queue.popleft()
            if (r, c) in exterior:
                continue
            exterior.add((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < height and 0 <= nc < width and key[nr][nc] == 0 and (nr, nc) not in exterior:
                    queue.append((nr, nc))
        for r in range(height):
            for c in range(width):
                if key[r][c] == 0 and (r, c) not in exterior:
                    out[r][c] = color
    return out


def component_boxes(grid):
    key = grid_key(grid)
    height, width = len(key), len(key[0])
    parent = {r * width + c: r * width + c for r in range(height) for c in range(width) if key[r][c]}
    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    for index in parent:
        r, c = divmod(index, width)
        for nr, nc in ((r + 1, c), (r, c + 1)):
            neighbor = nr * width + nc
            if nr < height and nc < width and neighbor in parent and key[r][c] == key[nr][nc]:
                parent[find(index)] = find(neighbor)
    groups = {}
    for index in parent:
        groups.setdefault(find(index), []).append(divmod(index, width))
    out = [list(row) for row in key]
    proposals = {}
    for cells in groups.values():
        color = key[cells[0][0]][cells[0][1]]
        for r in range(min(r for r, c in cells), max(r for r, c in cells) + 1):
            for c in range(min(c for r, c in cells), max(c for r, c in cells) + 1):
                if key[r][c] == 0:
                    proposals.setdefault((r, c), set()).add(color)
    for (r, c), colors in proposals.items():
        if len(colors) == 1:
            out[r][c] = next(iter(colors))
    return out


def compare_evidence(source_a, source_b, stdout_a, stdout_b, shape):
    return {'source_bytes_equal': source_a.encode() == source_b.encode(),
            'raw_stdout_bytes_equal': stdout_a.encode() == stdout_b.encode(),
            'normalized_distribution_equal': distribution_equal(strict_json(stdout_a, 65536), strict_json(stdout_b, 65536), shape)}


def average(values):
    require(bool(values), 'empty mean')
    return str(sum(values, Fraction()) / len(values))


def verify_payload(payload, mapping):
    """Semantic checks for an already pin-checked payload; source remains data."""
    exact_keys(payload, PAYLOAD_KEYS, 'payload')
    cases_raw = text_bytes(payload['cases_utf8'], 65536, 'cases')
    require(sha(cases_raw) == mapping['cases_sha256'], 'cases pin')
    cases = strict_json(cases_raw, 65536)
    constants = payload['prompt_constants']
    exact_keys(constants, {'API', 'FREE', 'LINKED'}, 'prompt constants')
    require(sha(canonical(constants)) == mapping['prompt_constants_sha256'], 'prompt constants pin')
    records = cases['records']
    require(type(records) is list and len(records) == 11, 'eleven heldout requests')
    record_by_id = {}
    for record in records:
        exact_keys(record, {'id', 'request', 'role', 'truth_by_world'}, 'case')
        require(type(record['id']) is str and record['id'] not in record_by_id, 'unique case identifier')
        require(record['role'] in ('transfer', 'retention', 'unknown_epoch'), 'case role')
        record_by_id[record['id']] = record
        for world in WORLDS:
            require(truth(record['request']['grid'], world) == record['truth_by_world'][world], 'independent case truth: ' + record['id'])
    require([sum(r['role'] == role for r in records) for role in ('transfer', 'retention', 'unknown_epoch')] == [5, 4, 2], 'case role counts')
    initial = cases['available_initial']
    for world in WORLDS:
        require(truth(initial['diagnostic_request']['grid'], world) == cases['diagnostic_truth_by_world'][world], 'independent diagnostic truth')
        for example in initial['training']:
            require(truth(example['input'], world) == example['output'], 'independent initial truth')
    exact_keys(payload['calls'], SLOTS, 'ten fixed calls')
    pins = mapping['selected_original_pins']
    carriers = {}
    costs = {'reserved_slots': 10, 'helper_attempts': 10, 'known_usage_calls': 10,
             'known_input_tokens': 0, 'known_output_tokens': 0, 'known_cached_input_tokens': 0,
             'cached_usage_unreported_calls': 0, 'unknown_usage_slots': [], 'call_wall_s': 0.0}
    native_wall_s = 0.0
    for slot in SLOTS:
        call = payload['calls'][slot]
        exact_keys(call, CALL_KEYS, 'call: ' + slot)
        require(call['terminal'] is True and type(call['exit_code']) is int and call['exit_code'] == 0 and call['event_types'] == ['turn.completed'] and call['tools'] == [], 'terminal tool-free call: ' + slot)
        for field, cap in (('prompt', 120000), ('response', 65536)):
            digest = sha(text_bytes(call[field], cap, field))
            require(digest == call[field + '_sha256'] == pins['cohort-v1/calls/' + slot + '/' + ('prompt.txt' if field == 'prompt' else 'response.txt')], 'original call bytes: ' + slot + '/' + field)
        exact_keys(call['usage'], {'input_tokens', 'output_tokens', 'cached_input_tokens'}, 'known usage')
        require(all(type(v) is int and v >= 0 for v in call['usage'].values()) and call['usage']['cached_input_tokens'] <= call['usage']['input_tokens'], 'usage and cached subset')
        require(costs['known_input_tokens'] < 300000 and costs['known_output_tokens'] < 50000, 'prefix observation ceiling')
        for key in ('input_tokens', 'output_tokens', 'cached_input_tokens'):
            costs['known_' + key] += call['usage'][key]
        for key in ('outer_wall_s', 'wall_ms'):
            require(type(call[key]) in (int, float) and math.isfinite(call[key]) and call[key] >= 0, 'known wall time')
        costs['call_wall_s'] += call['outer_wall_s']
        native_wall_s += call['wall_ms'] / 1000
        if slot == 'canary':
            require(call['response'].strip() == 'INDUCTION_ROUTE_OK' and call['source_sha256'] is None and call['method_record_sha256'] is None, 'canary carrier')
            continue
        body = strict_json(call['response'], 65536)
        exact_keys(body, {'source', 'method_record'}, 'source carrier')
        source_raw = text_bytes(body['source'], 24576, 'source')
        record_raw = text_bytes(body['method_record'], 4096, 'method record')
        require(bool(source_raw) and sha(source_raw) == call['source_sha256'] and sha(record_raw) == call['method_record_sha256'], 'carrier source/record hashes')
        carriers[slot] = body
    require(costs == payload['declared_costs'], 'independently recomputed declared costs')
    require(type(payload['captures']) is list and len(payload['captures']) == 100, 'exactly 100 captures')
    captures, forecasts = {}, {}
    expected = {(slot, record['id']) for slot in SLOTS[1:] for record in records} | {('m0', 'diagnostic')}
    for capture in payload['captures']:
        exact_keys(capture, CAPTURE_KEYS, 'capture')
        key = (capture['slot'], capture['record'])
        require(key in expected and key not in captures, 'unexpected or duplicate capture')
        slot, identifier = key
        require(type(capture['outer_bwrap_returncode']) is int and capture['outer_bwrap_returncode'] == 0 and all(capture[name] is None for name in ('observer_error', 'source_error', 'candidate_error')), 'successful capture taxonomy')
        require(capture['artifact_bytes'] == 0 and type(capture['artifact_bytes']) is int and capture['artifact_sha256'] == {} and capture['stderr_utf8'] == '', 'selected no-artifact/empty-stderr capture')
        base = 'cohort-v1/evaluations/' + slot + '/' + identifier + '/'
        require(capture['source_sha256'] == payload['calls'][slot]['source_sha256'] == pins[base + 'source.py'], 'capture source pin')
        for field, suffix, cap in (('request', 'request.runtime.json', 262144), ('stdout', 'stdout.bin', 65536), ('stderr', 'stderr.bin', 65536)):
            raw = text_bytes(capture[field + '_utf8'], cap, field)
            require(sha(raw) == capture[field + '_sha256'] == pins[base + suffix], 'capture byte pin: ' + field)
        require(len(capture['stdout_utf8'].encode()) + len(capture['stderr_utf8'].encode()) <= 65536, 'combined output cap')
        request = initial['diagnostic_request'] if identifier == 'diagnostic' else record_by_id[identifier]['request']
        expected_runtime = json.dumps(request, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
        require(capture['request_utf8'] == expected_runtime and set(strict_json(capture['request_utf8'])) == {'epoch', 'grid'}, 'exact runtime request')
        value = strict_json(capture['stdout_utf8'], 65536)
        parse_forecast(value, (len(request['grid']), len(request['grid'][0])))
        captures[key], forecasts[key] = capture, value
    require(set(captures) == expected, 'complete source/request cross-product')
    diagnostic_visible = {'forecast': forecasts['m0', 'diagnostic'], 'candidate_error': None, 'observer_error': None}
    prompt_facts = {}
    for slot in SLOTS:
        if slot == 'canary':
            require(payload['calls'][slot]['prompt'] == 'Return exactly INDUCTION_ROUTE_OK and nothing else. Do not use tools.', 'canary prompt')
            continue
        if slot == 'm0':
            facts = initial
            prefix = 'Induce an initial forecasting procedure from these raw observations.\n' + constants['API'] + '\n' + constants['FREE'] + '\nAVAILABLE_INITIAL_DATA\n'
        else:
            world = 'w-a' if slot.endswith('-a') else 'w-b'
            feedback = {'status': 'withheld'} if slot.startswith('masked-') else {'status': 'observed', 'epoch': initial['diagnostic_request']['epoch'], 'input': initial['diagnostic_request']['grid'], 'output': cases['diagnostic_truth_by_world'][world]}
            facts = {'initial': initial}
            if slot.startswith('fresh-'):
                prefix = 'Induce a forecasting procedure from all these raw observations.\n' + constants['API'] + '\n' + constants['FREE'] + '\nAVAILABLE_DATA\n'
            else:
                facts.update(own_initial_source=carriers['m0']['source'], own_initial_record=carriers['m0']['method_record'], own_diagnostic_capture=diagnostic_visible)
                prefix = 'Reconsider your own forecasting procedure. Return complete successor source.\n' + constants['API'] + '\n' + constants['LINKED' if '-linked' in slot else 'FREE'] + '\nAVAILABLE_DATA\n'
            facts['feedback'] = feedback
        require(payload['calls'][slot]['prompt'] == prefix + canonical(facts).decode(), 'exact prompt fact projection: ' + slot)
        prompt_facts[slot] = facts
    for left, right in (('actual-free-a', 'actual-linked-a'), ('actual-free-b', 'actual-linked-b'), ('masked-free', 'masked-linked')):
        require(prompt_facts[left] == prompt_facts[right], 'same facts for free/linked')
    scores = []
    for slot in SLOTS[1:]:
        condition = slot if slot == 'm0' or slot.startswith('masked-') else slot.rsplit('-', 1)[0]
        old_worlds = WORLDS if slot == 'm0' or slot.startswith('masked-') else ('w-a' if slot.endswith('-a') else 'w-b',)
        for record in records:
            for old_world in old_worlds:
                for later_world in WORLDS if record['role'] == 'unknown_epoch' else (old_world,):
                    scores.append({'slot': slot, 'condition': condition, 'record': record['id'], 'role': record['role'], 'old_world': old_world, 'later_world': later_world, 'loss': brier(forecasts[slot, record['id']], truth(record['request']['grid'], later_world))})
    require(len(scores) == 156, '156 weighted truth rows')
    conditions = {}
    for condition in ('m0', 'actual-free', 'actual-linked', 'masked-free', 'masked-linked', 'fresh'):
        conditions[condition] = {}
        for role in ('transfer', 'retention', 'unknown_epoch'):
            selected = [r['loss'] for r in scores if r['condition'] == condition and r['role'] == role]
            conditions[condition][role] = {'observed_scores': len(selected), 'mean_loss': average(selected)}
    require(conditions == payload['declared_conditions'], 'independently recomputed declared conditions')
    paired = []
    for suffix in ('a', 'b'):
        for record in (r for r in records if r['role'] == 'transfer'):
            losses = {row['slot']: row['loss'] for row in scores if row['record'] == record['id']}
            paired.append(losses['actual-linked-' + suffix] - losses['actual-free-' + suffix])
    primary = average(paired)
    require(primary == payload['declared_primary'], 'independently recomputed declared primary')
    comparisons = {}
    for left, right in (('m0', 'masked-free'), ('m0', 'masked-linked'), ('actual-free-a', 'actual-linked-a'), ('actual-free-b', 'actual-linked-b')):
        rows = {}
        for record in records:
            shape = (len(record['request']['grid']), len(record['request']['grid'][0]))
            rows[record['id']] = compare_evidence(carriers[left]['source'], carriers[right]['source'], captures[left, record['id']]['stdout_utf8'], captures[right, record['id']]['stdout_utf8'], shape)
        comparisons[left + ' vs ' + right] = {'source_bytes_equal': carriers[left]['source'] == carriers[right]['source'],
            'all_raw_stdout_bytes_equal': all(row['raw_stdout_bytes_equal'] for row in rows.values()),
            'all_normalized_distributions_equal': all(row['normalized_distribution_equal'] for row in rows.values()),
            'different_distribution_records': [name for name, row in rows.items() if not row['normalized_distribution_equal']]}
    agreement = []
    for index, example in enumerate(initial['training']):
        component, global_box = component_boxes(example['input']), truth(example['input'], 'w-b')
        require(component == global_box == example['output'], 'initial component/global agreement')
        agreement.append({'record': 'initial-' + str(index), 'component_equals_global': True})
    require(component_boxes(initial['diagnostic_request']['grid']) == truth(initial['diagnostic_request']['grid'], 'w-b'), 'diagnostic component/global agreement')
    distinguishers = [record['id'] for record in records if record['role'] == 'transfer' and component_boxes(record['request']['grid']) != truth(record['request']['grid'], 'w-b')]
    require(distinguishers == ['closed-diamond', 'separate-components'], 'component/global heldout distinguishers')
    b_masses = []
    for slot in ('actual-free-b', 'actual-linked-b'):
        for identifier in distinguishers:
            request = record_by_id[identifier]['request']
            parsed = parse_forecast(forecasts[slot, identifier], (len(request['grid']), len(request['grid'][0])))
            comp, global_box = grid_key(component_boxes(request['grid'])), grid_key(truth(request['grid'], 'w-b'))
            require(parsed.get(comp) == Fraction(19, 25) and parsed.get(global_box) == Fraction(19, 100), 'actual-B explicit masses')
            b_masses.append({'slot': slot, 'record': identifier, 'component_mass': str(parsed[comp]), 'global_mass': str(parsed[global_box])})
    return {'schema': 'verified-selected-induction-projection/1', 'experimental_calls': 10, 'source_captures': 100, 'weighted_truth_rows': 156,
            'primary_linked_minus_free': primary, 'conditions': conditions, 'costs': costs, 'known_native_wall_s': native_wall_s,
            'comparisons': comparisons, 'component_global_information': {'initial_agreements': agreement, 'diagnostic_agreement': True, 'withheld_distinguishers': distinguishers, 'actual_b_masses': b_masses,
                'boundary': 'Equal likelihood under these two explicit deterministic hypotheses on the supplied world-B examples/diagnostic; no full posterior over arbitrary functions or residual programs. Retained 4:1 is not refuted by those observations.'},
            'boundary': 'N=1 descriptive selected-artifact regrade. Source is inert data. Mapping/payload pins establish selected-byte consistency, not independently authenticated origin/time, full original-tree equality, new executions, source equivalence on all inputs, formation, or provider identity. Omitted native stdout/stderr and dependency closure are not verified.'}


def verify_projection(projection_path=HERE / 'projection.json.gz', mapping_path=HERE / 'projection-mapping.json'):
    document = load_projection(projection_path, mapping_path)
    report = verify_payload(document['payload'], document['mapping'])
    report['mapping_sha256'], report['payload_sha256'] = MAPPING_SHA256, PAYLOAD_SHA256
    return report


if __name__ == '__main__':
    print(json.dumps(verify_projection(), ensure_ascii=False, sort_keys=True, indent=2))
