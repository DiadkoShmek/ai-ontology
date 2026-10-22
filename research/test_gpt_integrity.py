"""Adversarial checks of saved GPT data, not additional model calls."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class GptIntegrityTest(unittest.TestCase):
    def copied(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);research=root/'research';research.mkdir()
        for name in ('gpt_profile_pilot','gpt_profile_pilot_v2','participation_pilot'):
            shutil.copytree(ROOT/'research'/name,research/name,
                            ignore=shutil.ignore_patterns('responses.jsonl','__pycache__'))
        shutil.copyfile(ROOT/'research/verify_gpt_profiles.py',research/'verify_gpt_profiles.py')
        return root

    def invoke(self,root,name):
        return subprocess.run(['python3','-O',str(root/'research/verify_gpt_profiles.py'),name],
                              text=True,capture_output=True)

    def rewrite(self,root,mutate,rehash=False):
        here=root/'research/gpt_profile_pilot_v2';p=here/'responses.jsonl.gz'
        rows=[json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()]
        mutate(rows[0])
        raw=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
        p.write_bytes(gzip.compress(raw,mtime=0))
        if rehash:
            for name in ('completion.json','results.json'):
                target=here/name;d=json.loads(target.read_text());d['raw_sha256']=hashlib.sha256(raw).hexdigest()
                target.write_text(json.dumps(d))

    def test_originals_under_optimization(self):
        for name in ('gpt_profile_pilot','gpt_profile_pilot_v2'):
            r=self.invoke(ROOT,name);self.assertEqual(r.returncode,0,r.stderr)

    def test_changed_prompt_rejected(self):
        root=self.copied();self.rewrite(root,lambda r:r.update(prompt=r['prompt']+' changed'))
        self.assertNotEqual(self.invoke(root,'gpt_profile_pilot_v2').returncode,0)

    def test_rehashed_prompt_still_rejected(self):
        root=self.copied()
        def change(r):
            r['prompt']+=' changed';r['prompt_sha256']=hashlib.sha256(r['prompt'].encode()).hexdigest()
        self.rewrite(root,change,rehash=True)
        r=self.invoke(root,'gpt_profile_pilot_v2')
        self.assertNotEqual(r.returncode,0);self.assertIn('prompt/history drift',r.stderr)

    def test_terminal_flag_cannot_override_native_metadata(self):
        root=self.copied();self.rewrite(root,lambda r:r.update(terminal=not r['terminal']),rehash=True)
        r=self.invoke(root,'gpt_profile_pilot_v2')
        self.assertNotEqual(r.returncode,0);self.assertIn('terminal drift',r.stderr)


if __name__=='__main__':unittest.main()
