"""Archive verification regressions; no inference, network or original mutation."""
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


class ArchiveIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('examples', 'research/continuity_pilot', 'research/continuity_pilot_v2'):
            shutil.copytree(ROOT / name, self.root / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'responses.jsonl'))
        for name in ('verify_studies.py', 'summarize_studies.py',
                     'study-summary.json',
                     'model-integration-results.json'):
            shutil.copy2(ROOT / 'research' / name, self.root / 'research' / name)
        subprocess.run(['git','init','--bare','--quiet',str(self.root/'.git')],check=True)
        gitdir=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--absolute-git-dir'],text=True).strip()
        (self.root/'.git/objects/info/alternates').write_text(str(Path(gitdir)/'objects')+'\n')

    def tamper(self, rehash=False):
        folder = self.root / 'research/continuity_pilot_v2'
        archive = folder / 'responses.jsonl.gz'
        rows = [json.loads(line) for line in gzip.decompress(archive.read_bytes()).splitlines()]
        rows[0]['messages'][1]['content'] = 'Not the frozen prompt'
        raw = ''.join(json.dumps(row) + '\n' for row in rows).encode()
        archive.write_bytes(gzip.compress(raw))
        if rehash:
            for name, field in (('results.json', 'raw_sha256'),
                                ('completion.json', 'response_sha256')):
                path = folder / name
                value = json.loads(path.read_text())
                value[field] = hashlib.sha256(raw).hexdigest()
                path.write_text(json.dumps(value))

    def run_python(self, args, optimize=None):
        env = {k: v for k, v in os.environ.items()
               if k not in ('PYTHONOPTIMIZE', 'PYTHONPATH')}
        if optimize is not None:
            env['PYTHONOPTIMIZE'] = optimize
        return subprocess.run([sys.executable, *args], cwd=self.root, env=env,
                              capture_output=True, text=True, timeout=60)

    def test_unchanged_archives_verify_with_optimization(self):
        result = self.run_python(['-O', 'research/verify_studies.py'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([r['calls'] for r in json.loads(result.stdout)], [192, 192])

    def test_prompt_tampering_fails_in_all_interpreter_modes(self):
        self.tamper()
        for flags, env in (([], None), (['-O'], None), ([], '1')):
            with self.subTest(flags=flags, env=env):
                result = self.run_python([*flags, 'research/verify_studies.py'], env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('response hash mismatch', result.stderr)
                self.assertNotIn('internally_consistent', result.stdout)

    def test_rehashing_does_not_replace_the_frozen_prompt(self):
        self.tamper(rehash=True)
        result = self.run_python(['-O', 'research/verify_studies.py'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('frozen prompt mismatch', result.stderr)

    def test_summary_rejects_changed_archive_under_optimization(self):
        self.tamper()
        # Call build only: a rejected summary must not overwrite a table.
        result = self.run_python(['-O', '-c',
            "import sys; sys.path.insert(0, 'research'); from summarize_studies import build; build()"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('response hash mismatch', result.stderr)


if __name__ == '__main__':
    unittest.main()
