import copy,hashlib,json,math,os,sqlite3,stat
from pathlib import Path

class AuditError(ValueError):
    pass

def _need(condition, reason):
    if not condition:
        raise AuditError(reason)

def _sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _bytes(path, cap=64 * 1024 * 1024):
    """Refuse symlinks, including dangling links, rather than follow evidence."""
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        _need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'not-regular-file:' + path.name)
        raw = stream.read(cap + 1)
    _need(len(raw) <= cap, 'evidence-size:' + path.name)
    return raw

def _unique(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, 'duplicate-json-key')
        result[key] = value
    return result

def _json(raw):
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=_unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(AuditError('nonfinite-json')))
    # json.loads also admits exponent overflow. Re-encoding must refuse it.
    json.dumps(value, allow_nan=False, ensure_ascii=True)
    return value

def _same(actual, expected, reason):
    # Python otherwise identifies True with 1, although the wire does not.
    _need(json.dumps(actual, sort_keys=True, ensure_ascii=True, allow_nan=False) ==
          json.dumps(expected, sort_keys=True, ensure_ascii=True, allow_nan=False), reason)

def _episode(episode, wrapper, s):
    """Replay only host receipt semantics, not controller execution."""
    e = s.environment
    case = s.case_for(wrapper)
    _need(type(episode) is dict, 'episode-missing')
    _need(episode.get('status') not in ('instrument-error', 'instrument-limit'), 'episode-instrument-fault')
    _need(episode.get('case_sha256') == _sha(e._wire(case)), 'episode-case-binding')
    settings = dict(e.DEFAULT_LIMITS, **s.LIMITS)
    _same(episode.get('limits'), settings, 'episode-limits')
    _same(episode.get('rights'), {'tools': ['search', 'read', 'answer', 'abstain'],
                                'costs': dict(e.COSTS), 'target_step': case['target_step']}, 'episode-rights')
    rows = episode.get('transcript')
    _need(type(rows) is list and len(rows) <= settings['max_steps'], 'episode-transcript')
    history, state, cost, native_wall, output_bytes = [], None, 0, 0.0, 0
    status = None
    documents = {d['document_id']: d for d in case['documents']}
    for index, row in enumerate(rows):
        slot = index + 1
        _need(status is None and cost + 2 <= settings['max_cost'], 'step-after-terminal-or-budget')
        _need(type(row) is dict and row.get('slot') == slot, 'step-order')
        request = {'task': e._task(case['task'], case['target_step']), 'history': copy.deepcopy(history),
                   'state': copy.deepcopy(state), 'remaining_budget': {
                       'steps': settings['max_steps'] - index, 'cost': settings['max_cost'] - cost}}
        _same(row.get('request'), request, 'request-chain')
        request_wire = e._wire(row['request'])
        _need(row.get('request_sha256') == _sha(request_wire), 'request-sha256')
        _need(len(e._wire(history)) <= settings['max_history_bytes'] and
              len(request_wire) <= s.sandbox.LIMITS['request_bytes'], 'unadmitted-request-size')
        _same(row.get('host_updates'), [], 'unexpected-host-update')
        capture = row.get('capture')
        _need(type(capture) is dict and type(capture.get('stdout')) is str and
              type(capture.get('stderr')) is str, 'capture-fields')
        _same(capture.get('limits'), dict(s.sandbox.LIMITS), 'capture-limits')
        wall = capture.get('wall_seconds')
        _need(type(wall) in (int, float) and math.isfinite(wall) and wall >= 0, 'capture-wall')
        native_wall += wall
        output_bytes += len(capture['stdout'].encode('utf-8')) + len(capture['stderr'].encode('utf-8'))
        error = capture.get('error')
        _need(error is None or type(error) is str, 'capture-error')
        _need(not (error or '').startswith('confinement-unavailable:'), 'confinement-unavailable')
        terminal = capture.get('terminal')
        if error is None:
            _need(type(capture.get('returncode')) is int and capture['returncode'] == 0, 'capture-returncode')
            _need(len(capture['stdout'].encode('utf-8')) + len(capture['stderr'].encode('utf-8')) <=
                  s.sandbox.LIMITS['output_bytes'], 'successful-capture-output-limit')
            _same(terminal, _json(capture['stdout'].encode('utf-8')), 'capture-terminal-wire')
            s.sandbox._json_bytes(terminal)
        else:
            _need(terminal is None, 'failed-capture-terminal')
        proposal_error = 'controller-failed' if error is not None else e._proposal(terminal, settings['max_state_bytes'])
        action = None if proposal_error else terminal['action']
        charge = e.COSTS['failed'] if proposal_error else e.COSTS[action['type']]
        receipt = {'slot': slot, 'kind': 'action-receipt'}
        saved_receipt = row.get('receipt', {})
        if saved_receipt.get('error') == 'wall-budget-refused':
            receipt.update(ok=False, error='wall-budget-refused')
            charge, status = e.COSTS['failed'], 'wall-limit'
        elif cost + e.COSTS['controller'] + charge > settings['max_cost']:
            receipt.update(ok=False, error='cost-budget-refused')
            charge, status = e.COSTS['failed'], 'cost-limit'
        elif proposal_error:
            receipt.update(ok=False, error=proposal_error)
        else:
            state = copy.deepcopy(terminal['state'])
            receipt['action'] = copy.deepcopy(action)
            kind = action['type']
            if kind == 'read':
                document = documents.get(action['document_id'])
                if document is not None and 'version' in action and action['version'] != document['version']:
                    document = None
                if document is None:
                    receipt.update(ok=False, error='not-found')
                else:
                    receipt.update(ok=True, result=copy.deepcopy(document))
            elif kind == 'search':
                terms = action['query'].casefold().split()
                matches = [d for d in documents.values() if all(t in (d['title'] + ' ' + d['text']).casefold() for t in terms)]
                receipt.update(ok=True, result=[{k: d[k] for k in ('document_id', 'version', 'scope', 'title')}
                                               for d in sorted(matches, key=lambda d: d['document_id'])])
            elif kind == 'answer':
                if slot < case['target_step']:
                    receipt.update(ok=False, error='before-target')
                else:
                    receipt.update(ok=True, result='answer-recorded')
                    status = 'answered'
            else:
                receipt.update(ok=True, result='abstention-recorded')
                status = 'abstained'
        _same(saved_receipt, receipt, 'receipt-replay')
        _same(row.get('tool_cost'), charge, 'tool-cost')
        cost += e.COSTS['controller'] + charge
        history.append(receipt)
    if status is None:
        status = ('step-limit' if len(rows) == settings['max_steps'] else
                  'cost-limit' if cost + 2 > settings['max_cost'] else 'wall-limit')
    _same(episode.get('status'), status, 'episode-status')
    _same(episode.get('history'), history, 'episode-history')
    accounting = episode.get('accounting', {})
    for key, expected in (('steps', len(rows)), ('cost', cost), ('native_wall_seconds', native_wall),
                          ('captured_output_utf8_bytes', output_bytes)):
        _same(accounting.get(key), expected, 'accounting:' + key)
    host_wall = accounting.get('host_wall_seconds')
    _need(type(host_wall) in (int, float) and math.isfinite(host_wall) and host_wall >= 0, 'host-wall')
    if status == 'wall-limit':
        _need(host_wall >= settings['max_wall_seconds'], 'unsupported-wall-limit')
    answers = [r['action'] for r in history if r.get('ok') and r.get('action', {}).get('type') == 'answer']
    expected_assessment = ({'evaluated': False, 'useful': False} if not answers else
                           e.assess_answer(answers[-1], case['oracle']))
    if status == 'abstained':
        expected_assessment = {'evaluated': True, 'useful': False, 'reason': history[-1]['action']['reason']}
    _same(episode.get('assessment'), expected_assessment, 'episode-assessment')
    return answers

def _record(row, result, wrapper, sqlite_path, s):
    _need(type(row) is dict, 'record-type')
    _need(not row.get('instrument_error'), 'record-instrument-fault')
    source, source_error = s.source_from(result)
    expected_source = _sha(source.encode('utf-8')) if source is not None else None
    _same(row.get('source_sha256'), expected_source, 'source-binding')
    _same(row.get('source_error'), source_error, 'source-error-binding')
    _need(row.get('wrapper_sha256') == _sha(s.wire(wrapper)), 'wrapper-binding')
    if source is None:
        _need(row.get('candidate_error') == 'unavailable-source' and row.get('success') is False,
              'unavailable-source-record')
        _need('episode' not in row and 'execution' not in row and not os.path.lexists(sqlite_path), 'effect-without-source')
        _need(not any(k in row for k in ('new_contract', 'old_contract', 'source_citation_recorded')), 'grade-without-source')
        return copy.deepcopy(row)
    answers = _episode(row.get('episode'), wrapper, s)
    if not answers:
        _need(row.get('candidate_error') == row['episode']['status'] and row.get('success') is False,
              'candidate-failure-record')
        _need('execution' not in row and not os.path.lexists(sqlite_path), 'effect-without-answer')
        _need(not any(k in row for k in ('new_contract', 'old_contract', 'source_citation_recorded')), 'grade-without-answer')
        return copy.deepcopy(row)
    try:
        plan = s.effects.parse_plan(answers[-1]['text'])
        _need(set(plan['release']) <= set(wrapper['manifest']['requested']), 'release-outside-request')
    except s.effects.InvalidPlan as exc:
        _need(row.get('candidate_error') == str(exc) and row.get('success') is False and
              not os.path.lexists(sqlite_path) and 'execution' not in row, 'invalid-plan-record')
        return copy.deepcopy(row)
    except AuditError:
        _need(row.get('candidate_error') == 'release outside requested fields' and row.get('success') is False and
              not os.path.lexists(sqlite_path) and 'execution' not in row, 'invalid-release-record')
        return copy.deepcopy(row)
    # Check regular bytes before SQLite opens it. The trusted caller owns this
    # directory; this is not a concurrent hostile-filesystem transaction.
    digest = _sha(_bytes(sqlite_path))
    new, old = s.grade_effect(sqlite_path, wrapper), s.grade_effect(sqlite_path, wrapper, old=True)
    actual = new['artifact']
    # The proposal must actually explain the reopened mechanical effects; merely
    # substituting an optimal SQLite database cannot repair a bad saved action.
    values = {n['id']: n['value'] for n in wrapper['manifest']['nodes']}
    _same(actual['released'], [{'field': f, 'value': values[f]} for f in plan['release']], 'plan-release-effect')
    original = {d['delivery_id']: d for d in wrapper['manifest']['deliveries']}
    expected_withdrawals = []
    removed = set()
    for ident in plan['withdraw']:
        previous = original.get(ident)
        status = ('not-found' if previous is None else 'not-delivered' if previous['status'] != 'delivered' else 'tombstoned')
        expected_withdrawals.append({'delivery_id': ident, 'status': status})
        if status == 'tombstoned':
            removed.add(ident)
    history = sorted(original.values(), key=lambda d: d['delivery_id'])
    _same(actual['history'], history, 'plan-history-effect')
    _same(actual['remaining'], [d for d in history if d['delivery_id'] not in removed], 'plan-remaining-effect')
    _same(actual['withdrawals'], expected_withdrawals, 'plan-withdraw-effect')
    _same(actual['notices'], [{'recipient': r, 'status': 'recorded-local' if wrapper['manifest']['consent'].get(r, False)
                              else 'denied-contact'} for r in plan['notify']], 'plan-notify-effect')
    _same(actual['unresolved'], [{'delivery_id': d} for d in plan['unresolved']], 'plan-unresolved-effect')
    _need(new['sqlite_sha256'] == digest and old['sqlite_sha256'] == digest, 'sqlite-readback-drift')
    _same(row.get('execution'), {'reopened': True, 'artifact': actual,
                               'boundary': 'Synthetic local SQLite effects; tombstones preserve historical delivery and do not undo recipient knowledge.'},
          'saved-execution-readback')
    _same(row.get('new_contract'), new, 'cached-new-contract')
    _same(row.get('old_contract'), old, 'cached-old-contract')
    _same(row.get('success'), new['success'], 'cached-success')
    document = s.case_for(wrapper)['documents'][0]
    citations = answers[-1]['citations']
    cited = bool(citations) and all(c['document_id'] == document['document_id'] and
        c['version'] == document['version'] and c['scope'] == document['scope'] and
        c['quote'] in document['text'] for c in citations)
    _same(row.get('source_citation_recorded'), cited, 'citation-record')
    validated = copy.deepcopy(row)
    validated.update(success=new['success'], new_contract=new, old_contract=old)
    validated['execution']['artifact'] = actual
    return validated