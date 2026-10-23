"""Post-run adversarial checks of the frozen repair measurement, including -O."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/"research/handoff_repair"


class RepairIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (SOURCE/"completion.json").exists():
            raise unittest.SkipTest("prospective model cohort not yet completed")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="handoff-integrity-")
        self.addCleanup(self.temp.cleanup)
        self.copy = Path(self.temp.name)
        for name in ("freeze.json", "cases.json", "completion.json", "episodes.json", "responses.jsonl.gz"):
            shutil.copyfile(SOURCE/name, self.copy/name)
        shutil.copytree(SOURCE/"artifacts", self.copy/"artifacts")

    def verify(self):
        code = ("import sys; from pathlib import Path; "
                "sys.path.insert(0,sys.argv[1]); from analyze import derive; "
                "derive(Path(sys.argv[2]))")
        return subprocess.run([sys.executable, "-O", "-c", code, str(SOURCE), str(self.copy)],
                              capture_output=True, timeout=30)

    def rewrite_rows(self, mutate):
        rows = [json.loads(x) for x in gzip.decompress((self.copy/"responses.jsonl.gz").read_bytes()).splitlines()]
        mutate(rows)
        raw = b"".join((json.dumps(row, ensure_ascii=False)+"\n").encode() for row in rows)
        (self.copy/"responses.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
        complete = json.loads((self.copy/"completion.json").read_text())
        complete["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        (self.copy/"completion.json").write_text(json.dumps(complete))

    def test_untouched_records_reproduce_under_optimization(self):
        run = self.verify()
        self.assertEqual(run.returncode, 0, run.stderr.decode())

    def test_coherently_rehashed_prompt_is_rejected(self):
        def mutate(rows):
            row = next(r for r in rows if r["arm"] == "exact")
            row["prompt"] += "\nAdditional unregistered instruction"
            row["prompt_sha256"] = hashlib.sha256(row["prompt"].encode()).hexdigest()
        self.rewrite_rows(mutate)
        self.assertNotEqual(self.verify().returncode, 0)

    def test_native_counter_disagreement_is_rejected(self):
        def mutate(rows):
            row = next(r for r in rows if r.get("usage"))
            row["usage"]["input_tokens"] += 1
        self.rewrite_rows(mutate)
        self.assertNotEqual(self.verify().returncode, 0)

    def test_terminal_flip_is_rejected(self):
        self.rewrite_rows(lambda rows: rows[0].update(terminal=not rows[0]["terminal"]))
        self.assertNotEqual(self.verify().returncode, 0)

    def test_changed_episode_score_is_rejected(self):
        episodes = json.loads((self.copy/"episodes.json").read_text())
        episodes[0]["primary"] = not episodes[0]["primary"]
        (self.copy/"episodes.json").write_text(json.dumps(episodes))
        self.assertNotEqual(self.verify().returncode, 0)

    def test_changed_delivered_file_is_rejected(self):
        target = next((self.copy/"artifacts").glob("*-exact/wire.json"))
        target.write_bytes(target.read_bytes()+b" ")
        self.assertNotEqual(self.verify().returncode, 0)


if __name__ == "__main__":
    unittest.main()
