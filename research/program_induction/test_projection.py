"""Saved evidence and synthetic forecast data only; no candidate execution."""
import copy
from fractions import Fraction
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import verify_projection as verifier


def forecast(*items):
    return {'hypotheses': [{'grid': [[color]], 'probability': probability} for color, probability in items]}


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = verifier.load_projection()
        cls.report = verifier.verify_payload(cls.document['payload'], cls.document['mapping'])

    def payload(self):
        return copy.deepcopy(self.document['payload'])

    def semantic(self, payload):
        return verifier.verify_payload(payload, self.document['mapping'])

    def test_fixed_saved_projection_regrades(self):
        self.assertEqual(self.report['experimental_calls'], 10)
        self.assertEqual(self.report['source_captures'], 100)
        self.assertEqual(self.report['weighted_truth_rows'], 156)
        self.assertGreater(Fraction(self.report['primary_linked_minus_free']), 0)
        self.assertEqual(self.report['costs']['known_input_tokens'], 166840)
        self.assertEqual(self.report['costs']['known_cached_input_tokens'], 61952)
        self.assertEqual(self.report['costs']['known_output_tokens'], 22006)

    def test_missing_capture_is_refused(self):
        payload = self.payload()
        payload['captures'].pop()
        with self.assertRaisesRegex(verifier.ProjectionError, '100 captures'):
            self.semantic(payload)

    def test_duplicate_capture_does_not_fill_missing_member(self):
        payload = self.payload()
        payload['captures'][1] = copy.deepcopy(payload['captures'][0])
        with self.assertRaisesRegex(verifier.ProjectionError, 'duplicate capture'):
            self.semantic(payload)

    def test_tampered_raw_stdout_is_refused(self):
        payload = self.payload()
        payload['captures'][0]['stdout_utf8'] += ' '
        with self.assertRaisesRegex(verifier.ProjectionError, 'capture byte pin'):
            self.semantic(payload)

    def test_rehashing_tampered_raw_stdout_does_not_change_original_pin(self):
        payload = self.payload()
        capture = payload['captures'][0]
        capture['stdout_utf8'] += ' '
        capture['stdout_sha256'] = verifier.sha(capture['stdout_utf8'].encode())
        with self.assertRaisesRegex(verifier.ProjectionError, 'capture byte pin'):
            self.semantic(payload)

    def test_declared_loss_is_recomputed(self):
        payload = self.payload()
        payload['declared_conditions']['actual-free']['transfer']['mean_loss'] = '0'
        with self.assertRaisesRegex(verifier.ProjectionError, 'declared conditions'):
            self.semantic(payload)

    def test_declared_primary_is_recomputed(self):
        payload = self.payload()
        payload['declared_primary'] = '0'
        with self.assertRaisesRegex(verifier.ProjectionError, 'declared primary'):
            self.semantic(payload)

    def test_extra_slot_and_capture_fields_refused(self):
        payload = self.payload()
        payload['calls']['replacement'] = copy.deepcopy(payload['calls']['m0'])
        with self.assertRaises(verifier.ProjectionError):
            self.semantic(payload)
        payload = self.payload()
        payload['captures'][0]['hidden'] = 'extra'
        with self.assertRaises(verifier.ProjectionError):
            self.semantic(payload)

    def test_unknown_usage_cannot_be_counted_as_zero(self):
        payload = self.payload()
        payload['calls']['m0']['usage']['input_tokens'] = None
        with self.assertRaisesRegex(verifier.ProjectionError, 'usage'):
            self.semantic(payload)

    def test_cached_input_is_subset(self):
        payload = self.payload()
        payload['calls']['canary']['usage']['cached_input_tokens'] = payload['calls']['canary']['usage']['input_tokens'] + 1
        with self.assertRaisesRegex(verifier.ProjectionError, 'cached subset'):
            self.semantic(payload)

    def test_native_terminal_and_typed_errors_are_checked(self):
        payload = self.payload()
        payload['calls']['m0']['terminal'] = 1
        with self.assertRaises(verifier.ProjectionError):
            self.semantic(payload)
        payload = self.payload()
        payload['captures'][0]['observer_error'] = 'observer-failure'
        with self.assertRaises(verifier.ProjectionError):
            self.semantic(payload)

    def test_duplicate_json_keys_and_nonfinite_values_refused(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'{"x":"\\ud800"}', b'{"\\ud800":0}', b'[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]'):
            with self.subTest(raw=raw):
                with self.assertRaises(verifier.ProjectionError):
                    verifier.strict_json(raw)

    def test_bad_forecast_grammar_is_refused(self):
        values = [forecast((True, '1')), forecast((0, '01')), forecast((0, '1/0')),
                  forecast((0, '1.0')), forecast((0, '2')), forecast((0, '1'), (0, '0')),
                  forecast((0, '1'), (1, '1'))]
        values.append({'hypotheses': [{'grid': [[0]], 'probability': 1}]})
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(verifier.ProjectionError):
                    verifier.parse_forecast(value, (1, 1))

    def test_same_top_grid_different_confidence_is_different_distribution(self):
        left, right = forecast((0, '4/5')), forecast((0, '3/5'))
        self.assertEqual(left['hypotheses'][0]['grid'], right['hypotheses'][0]['grid'])
        self.assertFalse(verifier.distribution_equal(left, right, (1, 1)))
        self.assertNotEqual(verifier.brier(left, [[0]]), verifier.brier(right, [[0]]))

    def test_normalization_handles_uniform_explicit_mass_and_residual(self):
        self.assertTrue(verifier.distribution_equal(forecast(), forecast((0, '1/5')), (1, 1)))
        self.assertFalse(verifier.distribution_equal(forecast(), forecast((0, '0')), (1, 1)))
        self.assertEqual(verifier.brier(forecast(), [[0]]), Fraction(4, 5))

    def test_full_support_union_with_different_residual_baselines(self):
        left = forecast((2, '1/5'), (3, '3/10'), (4, '3/10'))
        right = forecast((0, '1/10'), (1, '1/10'), (2, '1/5'))
        self.assertTrue(verifier.distribution_equal(left, right, (1, 1)))
        self.assertEqual(verifier.brier(left, [[0]]), Fraction(26, 25))
        self.assertEqual(verifier.brier(left, [[0]]), verifier.brier(right, [[0]]))

    def test_rational_order_and_raw_bytes_are_separate(self):
        left = forecast((0, '1/2'), (1, '1/4'))
        right = forecast((1, '2/8'), (0, '2/4'))
        result = verifier.compare_evidence('source A', 'source B', json.dumps(left), json.dumps(right), (1, 1))
        self.assertFalse(result['source_bytes_equal'])
        self.assertFalse(result['raw_stdout_bytes_equal'])
        self.assertTrue(result['normalized_distribution_equal'])

    def test_saved_different_sources_same_predictions_are_not_source_equivalence(self):
        comparison = self.report['comparisons']['actual-free-b vs actual-linked-b']
        self.assertFalse(comparison['source_bytes_equal'])
        self.assertTrue(comparison['all_normalized_distributions_equal'])
        other = self.report['comparisons']['actual-free-a vs actual-linked-a']
        self.assertFalse(other['all_normalized_distributions_equal'])

    def test_component_global_information_boundary(self):
        information = self.report['component_global_information']
        self.assertTrue(information['diagnostic_agreement'])
        self.assertEqual(information['withheld_distinguishers'], ['closed-diamond', 'separate-components'])
        self.assertTrue(all(row['component_mass'] == '19/25' and row['global_mass'] == '19/100' for row in information['actual_b_masses']))

    def test_pin_and_decompression_limits_are_not_rehashable_by_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mapping = root / 'mapping.json'
            mapping.write_bytes((verifier.HERE / 'projection-mapping.json').read_bytes())
            projection = root / 'projection.json.gz'
            changed = copy.deepcopy(self.document)
            changed['payload']['declared_primary'] = '0'
            changed['mapping']['payload_sha256'] = verifier.sha(verifier.canonical(changed['payload']))
            projection.write_bytes(gzip.compress(verifier.canonical(changed)))
            with self.assertRaisesRegex(verifier.ProjectionError, 'mapping pin'):
                verifier.load_projection(projection, mapping)
            projection.write_bytes(gzip.compress(b' ' * (verifier.MAX_JSON_BYTES + 1)))
            with self.assertRaisesRegex(verifier.ProjectionError, 'byte cap'):
                verifier.load_projection(projection, mapping)
            projection.write_bytes(b'x' * (verifier.MAX_COMPRESSED_BYTES + 1))
            with self.assertRaisesRegex(verifier.ProjectionError, 'file byte cap'):
                verifier.load_projection(projection, mapping)
            projection.write_bytes(b'\x1f\x8b\x08\x00' + b'\x00' * 6 + b'\xff' * 12)
            with self.assertRaisesRegex(verifier.ProjectionError, 'invalid gzip'):
                verifier.load_projection(projection, mapping)


if __name__ == '__main__':
    unittest.main()
