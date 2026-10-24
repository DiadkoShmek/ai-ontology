#!/usr/bin/env python3
"""Twelve adversarial DATA families; never execute an archived source body."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('trusted_projection_verifier', HERE / 'verify_projection.py')
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def rehash(document):
    document['mapping']['payload_sha256'] = v.sha(v.canonical(document['payload']))


def rebind_call(document, slot):
    p = document['payload']
    call = p['calls'][slot]
    body = v.strict(call['response_utf8'].encode())
    for name, raw in (('prompt', call['prompt_utf8'].encode()),
                      ('response', call['response_utf8'].encode()),
                      ('source', body['source'].encode()),
                      ('method_note', body['method_note'].encode())):
        call[name + '_sha256'] = v.sha(raw)
    document['mapping']['original_digests']['calls'][slot]['prompt'] = call['prompt_sha256']


def rebind_capture(document, capture):
    original = document['mapping']['original_digests']['captures'][capture['id']]
    for channel in ('request', 'stdout', 'stderr'):
        capture[channel + '_sha256'] = v.sha(capture[channel + '_utf8'].encode())
        original[channel] = capture[channel + '_sha256']
    original['source'] = capture['source_sha256']


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = v.load_projection()

    def rejected(self, change, reason=None):
        document = copy.deepcopy(self.original)
        change(document)
        rehash(document)
        if reason:
            with self.assertRaisesRegex(ValueError, reason):
                v.verify(document)
        else:
            with self.assertRaises((ValueError, KeyError, TypeError)):
                v.verify(document)

    def test_01_full_actual_readback(self):
        result = v.verify(copy.deepcopy(self.original))
        self.assertEqual((result['model_calls'], result['source_captures'], result['truth_rows']), (9, 133, 146))
        self.assertEqual(result['source_byte_changed_count'], 2)
        self.assertEqual(result['D_by_world'], {'u0': '0', 'u1': '0'})
        self.assertEqual(result['changed_distribution_count'], 0)
        self.assertEqual(result['retention_regression_count'], 0)
        self.assertEqual(result['M0_control_means']['u0:E0:transfer'], '3/32')
        self.assertEqual(result['M0_control_means']['u0:E1:transfer'], '1/16')
        self.assertEqual(result['M0_control_means']['u1:E0:transfer'], '11/32')
        self.assertEqual(result['M0_control_means']['u1:E1:transfer'], '3/16')
        costs = result['format_costs']
        self.assertEqual(costs['organized']['input_tokens'] - costs['flat']['input_tokens'], 2488)

    def test_02_external_mapping_payload_pins(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet, mapping = Path(tmp) / 'packet.gz', Path(tmp) / 'mapping.json'
            packet.write_bytes((HERE / 'projection.json.gz').read_bytes())
            mapping.write_bytes(v.canonical(self.original['mapping']) + b'\n')
            document = copy.deepcopy(self.original)
            document['payload']['task_utf8'] += ' '
            packet.write_bytes(gzip.compress(v.canonical(document), mtime=0))
            with self.assertRaisesRegex(ValueError, 'payload-pin'):
                v.load_projection(packet, mapping)
            packet.write_bytes((HERE / 'projection.json.gz').read_bytes())
            mapping.write_bytes(b'{}\n')
            with self.assertRaisesRegex(ValueError, 'external-mapping-equality'):
                v.load_projection(packet, mapping)
            changed = copy.deepcopy(self.original)
            changed['mapping']['selection'].append('coherent mapping change')
            packet.write_bytes(gzip.compress(v.canonical(changed), mtime=0))
            mapping.write_bytes(v.canonical(changed['mapping']) + b'\n')
            with self.assertRaisesRegex(ValueError, 'external-mapping-pin'):
                v.load_projection(packet, mapping)

    def test_03_compression_depth_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = Path(tmp) / 'packet.gz'
            packet.write_bytes(b'x' * 262145)
            with self.assertRaisesRegex(ValueError, 'compressed-cap'):
                v.load_projection(packet)
            packet.write_bytes(gzip.compress(b' ' * 2097153, mtime=0))
            with self.assertRaisesRegex(ValueError, 'decompressed-cap'):
                v.load_projection(packet)
        with self.assertRaisesRegex(ValueError, 'json-depth'):
            v.strict(b'[' * 34 + b'0' + b']' * 34)
        self.rejected(lambda d: d['payload']['calls']['m0'].__setitem__('prompt_utf8', 'x' * 196609), 'prompt-cap')

    def test_04_duplicate_nonfinite(self):
        for raw in (b'{"a":0,"a":1}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    v.strict(raw)
        document = copy.deepcopy(self.original)
        document['payload']['calls']['m0']['observer_elapsed_s'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'nonfinite-number'):
            v.verify(document)

    def test_05_capture_coverage_and_crosssource(self):
        self.rejected(lambda d: d['payload']['captures'].pop(), 'capture-count')
        self.rejected(lambda d: d['payload']['captures'].__setitem__(2, d['payload']['captures'][1]), 'capture-order-descriptor')
        def cross(d):
            c = d['payload']['captures'][37]
            c['source_sha256'] = '0' * 64
            rebind_capture(d, c)
        self.rejected(cross, 'capture-source')

    def test_06_coherently_rehashed_E1_request_drift(self):
        def attack(d):
            c = d['payload']['captures'][37]
            request = v.strict(c['request_utf8'].encode())
            request['evidence'][2]['observations'][1]['origin'] = 'o2'
            c['request_utf8'] = v.wire(request, ascii_only=True).decode()
            rebind_capture(d, c)
        self.rejected(attack, 'canonical-request-wire')

    def test_07_historical_capsule_view_repeats(self):
        def mutate_text(d, old, new):
            call = d['payload']['calls']['revision-01']
            self.assertIn(old, call['prompt_utf8'])
            call['prompt_utf8'] = call['prompt_utf8'].replace(old, new, 1)
            rebind_call(d, 'revision-01')
        self.rejected(lambda d: mutate_text(d, 'M0_SOURCE_UTF8_BYTES:', 'M9_SOURCE_UTF8_BYTES:'), 'length-marker')
        self.rejected(lambda d: mutate_text(d, '"parser_reason_or_null":null', '"parser_reason_or_null":true'), 'common-metadata-capsule')
        self.rejected(lambda d: mutate_text(d, '"seq":0', '"seq":9'), 'same-information-ledger')
        def repeat(d):
            call = d['payload']['calls']['revision-07']
            call['prompt_utf8'] += '\n'
            rebind_call(d, 'revision-07')
        self.rejected(repeat, 'view-end')

    def test_08_forecast_grammar_mass_labels(self):
        for raw in ('```json\n{}\n```', '{"distribution":{"o1":" 1"}}',
                    '{"distribution":{"o1":"1/2"}}', '{"distribution":{"unknown":"1"}}',
                    '{"distribution":{"o1":true}}', '{"distribution":{"o1":"1000000000/1000000000"}}',
                    '{"distribution":{"o1":"2"}}', '{"distribution":{"o1":"1","o1":"1"}}'):
            def attack(d, raw=raw):
                c = d['payload']['captures'][0]
                c['stdout_utf8'] = raw
                rebind_capture(d, c)
            with self.subTest(raw=raw):
                self.rejected(attack)
        _, probs = v.forecast(b'{"distribution":{"o1":"1"}}\n', ['o1', 'o2'])
        self.assertEqual(probs['o2'], 0)

    def test_09_scores_weights_retention(self):
        self.rejected(lambda d: d['payload']['captures'][0]['score_declarations']['u0'].__setitem__('valid_brier', '0'), 'saved-score-algebra')
        self.rejected(lambda d: d['payload']['declared_summary'].__setitem__('D_overall', '1/2'), 'summary-D_overall')
        self.rejected(lambda d: d['payload']['declared_summary'].__setitem__('retention_regression_count', 1), 'summary-retention_regression_count')
        self.rejected(lambda d: d['payload']['declared_summary']['transfer_source_means'].__setitem__('u0:revision-01', '0'), 'summary-transfer_source_means')

    def test_10_usage_bool_status_unknown(self):
        for field, value in (('input_tokens', True), ('cached_input_tokens', None), ('output_tokens', -1), ('cached_input_tokens', 999999999)):
            self.rejected(lambda d, field=field, value=value: d['payload']['calls']['m0']['usage'].__setitem__(field, value), 'usage-')
        self.rejected(lambda d: d['payload']['calls']['m0']['terminal'].__setitem__('exit_code', False), 'selected-terminal')
        self.rejected(lambda d: d['payload']['calls']['m0']['terminal'].__setitem__('group_closure', 'closed'), 'selected-terminal')
        self.rejected(lambda d: d['payload']['captures'][0].__setitem__('outer_returncode', False), 'capture-clean')
        self.rejected(lambda d: d['payload']['captures'][0].__setitem__('observer_error', 'unknown'), 'capture-clean')

    def test_11_future_query_extra_fields(self):
        def leakage(d):
            c = d['payload']['calls']['revision-01']
            c['prompt_utf8'] = c['prompt_utf8'].replace('"episode_id":"e01"', '"episode_id":"e05"', 1)
            rebind_call(d, 'revision-01')
        self.rejected(leakage, 'same-information-ledger')
        self.rejected(lambda d: d['payload'].__setitem__('extra', True), 'closed-schema')
        def extra_request(d):
            c = d['payload']['captures'][37]
            req = v.strict(c['request_utf8'].encode())
            req['configuration'] = {'hidden': True}
            c['request_utf8'] = v.wire(req, ascii_only=True).decode()
            rebind_capture(d, c)
        self.rejected(extra_request, 'canonical-request-wire')

    def test_12_archived_source_is_inert(self):
        document = copy.deepcopy(self.original)
        p = document['payload']
        call = p['calls']['revision-01']
        carrier = v.strict(call['response_utf8'].encode())
        before = len(carrier['source'].encode())
        carrier['source'] = "raise RuntimeError('ARCHIVED SOURCE EXECUTED')\n"
        call['response_utf8'] = v.wire(carrier).decode()
        rebind_call(document, 'revision-01')
        for capture in p['captures']:
            if capture['source_slot'] == 'revision-01':
                capture['source_sha256'] = call['source_sha256']
                rebind_capture(document, capture)
        p['declared_summary']['format_costs']['flat']['source_bytes'] += len(carrier['source'].encode()) - before
        rehash(document)
        result = v.verify(document)
        self.assertEqual(result['truth_rows'], 146)


if __name__ == '__main__':
    unittest.main(verbosity=2)
