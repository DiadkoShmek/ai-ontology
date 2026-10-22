import ast
import hashlib
import json
from pathlib import Path
import unittest

from receipt_replay import run_cases

HERE = Path(__file__).resolve().parent


class EngineeringCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_cases()

    def test_committed_result_is_reconciled_instead_of_refused(self):
        case = self.result['commit_before_receipt_error']
        self.assertEqual(case['before'], {'first_status': 'REFUSED', 'last_status': 'REFUSED',
                                        'events': 1, 'append_calls': 1})
        self.assertEqual(case['after'], {'first_status': 'recorded', 'last_status': 'recorded',
                                       'events': 1, 'append_calls': 1})

    def test_unknown_does_not_turn_into_permission_to_append(self):
        case = self.result['uncertainty_survives_input_read_failure']
        self.assertEqual(case['intermediate'], {'first_status': 'UNCONFIRMED', 'last_status': 'recorded',
                                              'events': 1, 'append_calls': 2})
        self.assertEqual(case['after'], {'first_status': 'UNCONFIRMED', 'last_status': 'UNCONFIRMED',
                                       'events': 0, 'append_calls': 1})

    def test_published_function_bodies_match_extraction_manifest(self):
        manifest = json.loads((HERE / 'provenance.json').read_text())
        for item in manifest['sources']:
            with self.subTest(symbol=item['symbol'], file=item['published_file']):
                source = (HERE / item['published_file']).read_text()
                node = next(n for n in ast.parse(source).body
                            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                            and n.name == item['symbol'])
                self.assertEqual(hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest(),
                                 item['body_sha256'])


if __name__ == '__main__':
    unittest.main()
