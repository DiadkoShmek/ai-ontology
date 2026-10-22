import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ParticipationVerifierTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        shutil.copytree(ROOT/'research/participation_pilot', self.root/'research/participation_pilot',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'responses.jsonl'))
        shutil.copy2(ROOT/'research/verify_participation.py', self.root/'research/verify_participation.py')

    def run_verifier(self):
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONOPTIMIZE')}
        return subprocess.run([sys.executable, '-O', 'research/verify_participation.py'],
                              cwd=self.root, env=env, capture_output=True, text=True, timeout=60)

    def tamper(self, rehash=False):
        folder = self.root/'research/participation_pilot'
        archive = folder/'responses.jsonl.gz'
        rows = [json.loads(line) for line in gzip.decompress(archive.read_bytes()).splitlines()]
        rows[0]['messages'][-1]['content'] = 'Not the frozen question'
        raw = ''.join(json.dumps(row)+'\n' for row in rows).encode()
        archive.write_bytes(gzip.compress(raw))
        if rehash:
            path = folder/'completion.json'
            value = json.loads(path.read_text())
            value['response_sha256'] = hashlib.sha256(raw).hexdigest()
            path.write_text(json.dumps(value))

    def test_complete_original_cohort_verifies_under_optimization(self):
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['calls'], 136)

    def test_changed_archive_fails_under_optimization(self):
        self.tamper()
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('response hash mismatch', result.stderr)

    def test_rehash_does_not_replace_recorded_history(self):
        self.tamper(rehash=True)
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('request history mismatch', result.stderr)


if __name__ == '__main__':
    unittest.main()
