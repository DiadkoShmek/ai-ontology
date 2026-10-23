"""Selected offline readback only; run with python3 -I -S -B. No model/controller replay."""
import ast,base64,copy,gzip,hashlib,importlib.util,io,json,os,re,sys,tempfile,types
from pathlib import Path
ARCHIVE_CAP=134217728
SQLITE_CAP=4194304
_PRIVATE=re.compile(r"/home/[^/]+/|\.codex-lab|\b(?:council|strategy|intel)\b",re.IGNORECASE)
class ProjectionError(ValueError):
    pass

def _need(condition, reason):
    if not condition:
        raise ProjectionError(reason)

def _wire(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(',', ':')).encode('ascii')

def _sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _load_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ProjectionError('nonfinite JSON')))
    _wire(value)
    return value

def _scan(value):
    """Conservative publication screen, not a general secret detector."""
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is str:
            _need(_PRIVATE.search(item) is None, 'private contamination refused')
        elif type(item) is dict:
            pending.extend(item.keys()); pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)

def _unpack(value, cap):
    _need(type(value) is str and len(value) <= ((cap + 2) // 3) * 4, 'encoded byte cap')
    raw = base64.b64decode(value, validate=True)
    _need(len(raw) <= cap, 'decoded byte cap')
    return raw

def _sqlite_bytes(payload, key):
    entry = payload['sqlite'][key]
    _need(type(entry) is dict and set(entry) == {'sha256'}, 'SQLite reference shape')
    digest = entry['sha256']
    _need(type(digest) is str and re.fullmatch(r'[0-9a-f]{64}', digest), 'SQLite reference digest')
    raw = _unpack(payload['sqlite_blobs'][digest], SQLITE_CAP)
    _need(_sha(raw) == digest, 'SQLite byte digest')
    return raw

def _inflate_record(row):
    """Restore only omitted non-visible byte counts for the frozen cost checker.

    Spaces are NOT claimed as original stderr. Model-visible requests/history,
    proposals and stdout are retained exactly. Native error detail was omitted.
    """
    restored = copy.deepcopy(row)
    for step in restored.get('episode', {}).get('transcript', []):
        capture = step['capture']
        count = capture.pop('stderr_utf8_bytes')
        _need(type(count) is int and 0 <= count <= 196608, 'stderr count')
        capture['stderr'] = ' ' * count
        capture['error'] = capture.pop('error_class')
    return restored

def _mechanical(plan, manifest, artifact):
    """Independent check that a control's proposed actions explain its rows."""
    values = {n['id']: n['value'] for n in manifest['nodes']}
    history = sorted(manifest['deliveries'], key=lambda d: d['delivery_id'])
    delivered = {d['delivery_id']: d for d in history}
    removed, withdrawals = set(), []
    for ident in plan['withdraw']:
        previous = delivered.get(ident)
        status = 'not-found' if previous is None else 'not-delivered' if previous['status'] != 'delivered' else 'tombstoned'
        withdrawals.append({'delivery_id': ident, 'status': status})
        if status == 'tombstoned': removed.add(ident)
    expected = {'released': [{'field': f, 'value': values[f]} for f in plan['release']],
                'history': history, 'remaining': [d for d in history if d['delivery_id'] not in removed],
                'withdrawals': withdrawals,
                'notices': [{'recipient': r, 'status': 'recorded-local' if manifest['consent'].get(r, False)
                             else 'denied-contact'} for r in plan['notify']],
                'unresolved': [{'delivery_id': d} for d in plan['unresolved']]}
    _need(all(_wire(artifact[k]) == _wire(v) for k, v in expected.items()), 'control mechanical effect')

def _load_technical(sources, expected, folder):
    """Import only bytes bound by the trusted verifier's embedded source pins."""
    _need(set(sources) == set(expected), 'selected source set')
    files = {}
    for relative, entry in sources.items():
        _need(relative.startswith('technical/') and len(Path(relative).parts) == 2, 'source path')
        raw = _unpack(entry['base64'], 512 * 1024)
        _need(_sha(raw) == expected[relative] == entry['sha256'], 'selected source digest')
        raw.decode('utf-8', 'strict')
        _scan(raw.decode('utf-8'))
        path = folder / Path(relative).name
        path.write_bytes(raw)
        files[path.name] = path
    names = ('sandbox', 'environment', 'release_workflow', 'clearance_policy', 'study_fragment', 'audit_fragment')
    _need(set(files) == {n + '.py' for n in names}, 'technical module set')
    previous = {name: sys.modules.get(name) for name in names}
    bytecode = sys.dont_write_bytecode
    loaded = {}
    try:
        sys.dont_write_bytecode = True
        for name in names:
            spec = importlib.util.spec_from_file_location(name, files[name + '.py'])
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
        fragment = loaded['study_fragment']
        fragment.environment = loaded['environment']
        fragment.sandbox = loaded['sandbox']
        return fragment, loaded['audit_fragment']
    finally:
        sys.dont_write_bytecode = bytecode
        for name, prior in previous.items():
            if prior is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prior

def _verify_archive(path, expected):
    """Portable offline verification. No controller/provider/executor invocation.

    expected must come from a trusted exported verifier/mapping, not from the
    untrusted archive being checked. Coherent replacement of both is not attested.
    """
    with Path(path).open('rb') as stream:
        _need(os.fstat(stream.fileno()).st_size <= ARCHIVE_CAP, 'compressed archive cap')
        with gzip.GzipFile(fileobj=stream, mode='rb') as zipped:
            raw = zipped.read(ARCHIVE_CAP + 1)
    _need(len(raw) <= ARCHIVE_CAP, 'decompressed archive cap')
    bundle = _load_json(raw)
    _need(bundle.get('schema') == 'selected-clearance-projection/2', 'projection schema')
    _need(bundle.get('mapping') == expected, 'trusted projection mapping')
    payload = bundle['payload']
    _need(_sha(_wire(payload)) == expected['payload_sha256'], 'projection payload digest')
    _scan({k: v for k, v in payload.items() if k not in ('sources', 'sqlite', 'sqlite_blobs')})
    _need(set(payload['sqlite_blobs']) == {entry['sha256'] for entry in payload['sqlite'].values()},
          'SQLite blob set')
    cases_raw = payload['cases_utf8'].encode('utf-8')
    _need(_sha(cases_raw) == expected['cases_sha256'], 'exact cases digest')
    data = _load_json(cases_raw)
    calls = payload['calls']
    units = data['units']
    ids = [u['id'] for u in units]
    expected_ids = {'canary'} | {u + '-m0' for u in ids} | {u + '-' + a for u, a in data['revision_order']}
    _need(len(ids) == expected['units'] and len(set(ids)) == len(ids) and
          all(type(uid) is str and re.fullmatch(r'u[0-9]+', uid) for uid in ids), 'unit identities')
    arms = ('ordinary_actual', 'linked_actual', 'ordinary_masked', 'linked_masked', 'fresh')
    _need({tuple(item) for item in data['revision_order']} == {(uid, arm) for uid in ids for arm in arms} and
          len(data['revision_order']) == len(ids) * 5, 'revision schedule')
    _need(set(calls) == expected_ids and len(calls) == len(ids) * 6 + 1, 'call denominator')
    for ident, call in calls.items():
        _need(set(call) == {'call_id', 'prompt', 'prompt_sha256', 'response', 'response_sha256',
                            'source_sha256', 'source_error', 'terminal', 'completion', 'usage'}, 'public call fields')
        _need(call['call_id'] == ident and type(call['terminal']) is bool, 'public call identity')
        _need(_sha(call['prompt'].encode('utf-8')) == call['prompt_sha256'] and
              _sha(call['response'].encode('utf-8')) == call['response_sha256'], 'prompt/response digest')
        _need(set(call['completion']) <= {'exit_code', 'event_types', 'failure_class'}, 'completion whitelist')
        for key, number in call['usage'].items():
            _need(key in ('input_tokens', 'output_tokens', 'cached_input_tokens') and
                  type(number) is int and number >= 0, 'numeric usage whitelist')
        if 'cached_input_tokens' in call['usage'] and 'input_tokens' in call['usage']:
            _need(call['usage']['cached_input_tokens'] <= call['usage']['input_tokens'], 'cached usage')
    _need(calls['canary']['terminal'] and calls['canary']['response'].strip() == '{"ready":true}', 'canary')
    _need(calls['canary']['prompt'] == 'Use no tools. Return exactly {"ready":true} and no other text.', 'canary prompt')
    rows_out, used_sqlite = {}, set()
    with tempfile.TemporaryDirectory(prefix='selected-clearance-verification-') as temporary:
        root = Path(temporary)
        s, a = _load_technical(payload['sources'], expected['selected_source_sha256'], root)
        _need(payload['prompt_contract'] == {k: getattr(s, k) for k in ('INTERFACE', 'OLD', 'NEW', 'SCAFFOLD')}, 'prompt contract')
        def generation(ident):
            call = calls[ident]
            result = {'terminal': call['terminal'], 'response': call['response']}
            source, error = s.source_from(result)
            _need(call['source_sha256'] == (_sha(source.encode('utf-8')) if source is not None else None) and
                  call['source_error'] == error, 'generation/source binding')
            if call['terminal']:
                _need(call['completion'] == {'exit_code': 0, 'event_types': ['turn.completed']}, 'terminal completion')
            else:
                _need(call['completion'].get('failure_class') == 'generation-timeout', 'nonterminal class')
            return result
        def record(row, result, wrapper, key):
            restored = _inflate_record(row)
            sqlite_path = root / (key + '.sqlite')
            source, _ = s.source_from(result)
            has_effect = 'execution' in row
            _need((key in payload['sqlite']) == has_effect, 'SQLite presence binding')
            if has_effect:
                raw_db = _sqlite_bytes(payload, key)
                _scan(raw_db.decode('utf-8', 'ignore'))
                sqlite_path.write_bytes(raw_db)
                used_sqlite.add(key)
            return a._record(restored, result, wrapper, sqlite_path, s)
        for unit in units:
            uid = unit['id']
            m0 = generation(uid + '-m0')
            _need(calls[uid + '-m0']['prompt'] == s.prompt_m0(), 'M0 prompt reconstruction')
            initial = record(payload['initial'][uid], m0, unit['initial'], uid + '-initial')
            results = {'m0': m0}
            for arm in ('ordinary_actual', 'linked_actual', 'ordinary_masked', 'linked_masked', 'fresh'):
                ident = uid + '-' + arm
                results[arm] = generation(ident)
                prompt = s.prompt_fresh(unit['initial']) if arm == 'fresh' else s.prompt_revision(m0, unit['initial'], initial, arm)
                _need(calls[ident]['prompt'] == prompt, 'revision/fresh prompt reconstruction')
            rows_out[uid] = {}
            for arm, result in results.items():
                rows = payload['observations'][uid][arm]
                _need(type(rows) is list and len(rows) == len(unit['transfer']), 'planned transfer rows')
                rows_out[uid][arm] = [record(row, result, wrapper, uid + '-' + arm + '-' + str(i))
                                     for i, (row, wrapper) in enumerate(zip(rows, unit['transfer']))]
        if expected['evidence_phase'] == 'separate offline reproduction':
            phase = payload['reproduction']
            _need(expected['original_status'] == 'interrupted/partial' and expected['original_registered_primary'] is None,
                  'original interruption must remain explicit')
            _need(phase['original_status'] == 'interrupted/partial' and phase['original_primary'] is None and
                  phase['model_calls_planned'] == 0 and phase['initial_reruns_planned'] == 0 and
                  phase['independent_preregistration'] is False, 'reproduction scope')
            schedule = phase['schedule']
            expected_schedule = []
            for unit in units:
                for arm in ('m0', 'ordinary_actual', 'linked_actual', 'ordinary_masked', 'linked_masked', 'fresh'):
                    for i, wrapper in enumerate(unit['transfer']):
                        call_id = unit['id'] + '-' + arm
                        expected_schedule.append({'id': call_id + '-' + str(i), 'unit': unit['id'], 'arm': arm,
                            'index': i, 'call_id': call_id, 'wrapper_sha256': _sha(s.wire(wrapper)),
                            'case_sha256': _sha(s.environment._wire(s.case_for(wrapper)))})
            _need(schedule == expected_schedule and phase['planned_episodes'] == len(schedule), 'reproduction full schedule')
            _need(set(payload['reproduction_records']) == {x['id'] for x in schedule}, 'reproduction record set')
            _need(len(phase['overlap']) == len(schedule) and {x['id'] for x in phase['overlap']} ==
                  {x['id'] for x in schedule}, 'overlap status denominator')
            for item in schedule:
                binding = payload['reproduction_records'][item['id']]
                intent = binding['intent']
                required = {k: item[k] for k in ('id', 'call_id', 'wrapper_sha256', 'case_sha256')}
                required.update(plan_sha256=expected['reproduction_plan_sha256'],
                                source_sha256=calls[item['call_id']]['source_sha256'],
                                source_error=calls[item['call_id']]['source_error'])
                _need({k: v for k, v in intent.items() if k != 'at'} == required, 'reproduction intent view')
                _need(binding['record_binding'] == {'id': item['id'], 'plan_sha256': expected['reproduction_plan_sha256'],
                      'intent_sha256': binding['original_intent_sha256']}, 'reproduction record/intention binding')
                row = payload['observations'][item['unit']][item['arm']][item['index']]
                _need(binding['projected_row_sha256'] == _sha(_wire(row)), 'reproduction projected row binding')
            for pair in phase['overlap']:
                item = next(x for x in schedule if x['id'] == pair['id'])
                row = rows_out[item['unit']][item['arm']][item['index']]
                artifact = row.get('execution', {}).get('artifact')
                _need(pair['reproduction']['success'] == row['success'] and
                      pair['reproduction']['artifact_sha256'] == (_sha(s.wire(artifact)) if artifact is not None else None),
                      'reproduction overlap observation')
                previous = pair['original']
                _need(previous['status'] in ('bound-observation', 'sqlite-only', 'missing', 'unbound-record-and-sqlite',
                                             'unbound-failed-capture'), 'original overlap status')
                if previous['status'] != 'bound-observation':
                    _need(previous['success'] is None and previous['artifact_sha256'] is None, 'unobserved original is not failure')
                else:
                    _need(type(previous['success']) is bool, 'bound original observation')
                score_difference = (previous['success'] != row['success'] if previous['success'] is not None else None)
                old_digest, new_digest = previous['artifact_sha256'], pair['reproduction']['artifact_sha256']
                artifact_difference = old_digest != new_digest if old_digest is not None and new_digest is not None else None
                _need(pair['score_disagreement'] is score_difference and
                      pair['artifact_disagreement'] is artifact_difference, 'overlap disagreements')
        controls = payload['authored_controls']
        expected_controls = {u['id'] + '-' + str(i) + '-' + c for u in units for i in range(len(u['transfer']))
                             for c in ('generic', 'old-content', 'withhold', 'all-release')}
        _need(len(controls) == len(expected_controls) and {r['id'] for r in controls} == expected_controls, 'authored control set')
        unit_map = {u['id']: u for u in units}
        for row in controls:
            wrapper = unit_map[row['unit']]['transfer'][row['case']]
            ident = row['unit'] + '-' + str(row['case']) + '-' + row['control']
            _need(ident == row['id'], 'control identity')
            plan = (s.policy.baseline_plan(wrapper, old=row['control'] == 'old-content')
                    if row['control'] in ('generic', 'old-content') else
                    {'release': wrapper['manifest']['requested'] if row['control'] == 'all-release' else [],
                     'withdraw': [], 'notify': [], 'unresolved': []})
            _need(row['plan'] == plan, 'control plan')
            key = 'control-' + ident
            raw_db = _sqlite_bytes(payload, key)
            _scan(raw_db.decode('utf-8', 'ignore'))
            path = root / (key + '.sqlite'); path.write_bytes(raw_db)
            used_sqlite.add(key)
            assessment = s.grade_effect(path, wrapper)
            _mechanical(plan, wrapper['manifest'], assessment['artifact'])
            _need(assessment == row['assessment'], 'control artifact regrade')
        _need(used_sqlite == set(payload['sqlite']), 'orphan SQLite bytes')
    by_arm = {arm: sum(row['success'] is True for unit in rows_out.values() for row in unit[arm])
              for arm in ('m0', 'ordinary_actual', 'linked_actual', 'ordinary_masked', 'linked_masked', 'fresh')}
    return {'verified': True, 'evidence_phase': expected['evidence_phase'],
            'original_status': expected['original_status'], 'original_registered_primary': expected.get('original_registered_primary'),
            'model_calls_in_evidence_phase': 0 if expected['evidence_phase'] == 'separate offline reproduction' else len(calls),
            'provided_original_generation_calls': len(calls),
            'planned_calls': 0 if expected['evidence_phase'] == 'separate offline reproduction' else len(calls),
            'planned_transfer_per_arm': sum(len(u['transfer']) for u in units),
            'regraded_successes': by_arm, 'sqlite_files': len(used_sqlite),
            'boundary': 'Selected portable consistency/readback; not authenticated provenance, private full-tree equality or independent preregistration.'}

EXPECTED={'local_freeze_sha256': 'cff5a199a7806e990edb39d7c3b61f895503838e70cf9d68e8b4689298a737c0', 'original_freeze_status': 'private/local; not independently preregistered', 'original_study_sha256': 'ac0782c6352df48e4bdc369661f0ae14e09cd6ac8c01bb5bbba3377db15b4d23', 'same_source_tree': False, 'independent_preregistration': False, 'projection_generator_sha256': 'f467483a56cb6b7183be0451711958007a643d162fd26fab0faec270ac6d6f63', 'projection_generated_after_original_freeze': True, 'units': 8, 'cases_sha256': '35d14b1198e60b14e1d4db502b670a104aebf76e333f6b96f7e1e067d9bd9e70', 'selected_source_sha256': {'technical/sandbox.py': 'cccdf962bfde34180fe84c1e6f9fd24d4c5aa6763a25785d732732c720928dc1', 'technical/environment.py': '8d56805e0af0a8314810d9b7098436c69a56b947733e292d9420e218505c9a54', 'technical/release_workflow.py': '80de6f29d1f5df15bbd675aabbcf11928df14377a4ebbaa259de02c1b15d0ffa', 'technical/clearance_policy.py': 'a5b9ae9d9bc669e16f0de61af37f2d7c2858d46f0ce83a3336ed854e9375aff8', 'technical/study_fragment.py': '62d0f8414798e5634113f9458edcbbefcc3875bb204b22b73e271881cff8b8d8', 'technical/audit_fragment.py': '3767b94d9420edacaa613df9f2e48771e147c4fc311c77bf087a98ab49bfdd16'}, 'source_projection': {'technical/sandbox.py': {'kind': 'exact selected source', 'original_sha256': 'cccdf962bfde34180fe84c1e6f9fd24d4c5aa6763a25785d732732c720928dc1'}, 'technical/environment.py': {'kind': 'exact selected source', 'original_sha256': '8d56805e0af0a8314810d9b7098436c69a56b947733e292d9420e218505c9a54'}, 'technical/release_workflow.py': {'kind': 'exact selected source', 'original_sha256': '80de6f29d1f5df15bbd675aabbcf11928df14377a4ebbaa259de02c1b15d0ffa'}, 'technical/clearance_policy.py': {'kind': 'exact selected source', 'original_sha256': 'a5b9ae9d9bc669e16f0de61af37f2d7c2858d46f0ce83a3336ed854e9375aff8'}, 'technical/study_fragment.py': {'kind': 'exact selected function bodies and literal constants', 'original_sha256': 'ac0782c6352df48e4bdc369661f0ae14e09cd6ac8c01bb5bbba3377db15b4d23', 'functions': ['wire', 'sha', 'source_from', 'case_for', 'grade_effect', 'prompt_m0', 'feedback', 'prompt_revision', 'prompt_fresh']}, 'technical/audit_fragment.py': {'kind': 'exact selected offline receipt/artifact validation functions', 'original_sha256': '9e2a14fd8d62b1777dbf906c15addf571e75dc2954dde4181ec8ecb6ca965754', 'functions': ['_need', '_sha', '_bytes', '_unique', '_json', '_same', '_episode', '_record']}}, 'payload_sha256': '90e09487774066a467a4b1f746113fe41bde8c3b1936ce9fd829780ef79de96e', 'sqlite_storage': 'content-addressed exact byte blobs; every episode retains its own reference', 'omitted': ['native thread/session identifiers and arbitrary native error text', 'non-visible controller stderr bytes (only UTF8 byte count retained)', 'private orchestration, inference helper, runtime absolute paths and internal planning', 'Original interrupted transfer bytes are not republished; overlap statuses/digests are a selected verified view, not original completion.'], 'limits': 'Publication screen is not a general secret detector. No authenticated origin or independent registration claim.', 'evidence_phase': 'separate offline reproduction', 'original_status': 'interrupted/partial', 'original_registered_primary': None, 'reproduction_plan_sha256': 'aeb6e1bc5ac762872deaadb19951f40e4ddbf45f2cfa6be27b7208ac6b0f35a2', 'reproduction_observer_source_sha256': {'REPRODUCTION_PROTOCOL.md': '14f9d419a6d9d6d97f995d5e78a7e645c0035d2dfde7b6fde4184c6495e4454e', 'reproduce.py': 'aa48dce9164298cfdd1ca148704a13bc97e14c38f1fc53fc5c5dec664f0f04c4', 'supplementary_readout.py': 'f9d80221f508fed9b5706ba5e785414ff1920db4e879e098b3a17bf99b3987e6', 'test_reproduce.py': '692346656196bf17943a021427d4954afc1ec3f25b9cad180e9a3d8c04f565a8'}}
if __name__=="__main__":
    print(json.dumps(_verify_archive(sys.argv[1],EXPECTED),sort_keys=True))
