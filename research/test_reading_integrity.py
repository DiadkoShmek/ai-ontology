"""Counterexamples for the saved-data reading-transfer verifier."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ReadingIntegrityTest(unittest.TestCase):
    def copied(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        (root/'research').mkdir();(root/'examples').mkdir()
        for name in ('transfer_reading','transfer_calibration_v3','gpt_profile_pilot_v2','participation_pilot'):
            shutil.copytree(ROOT/'research'/name,root/'research'/name,
                            ignore=shutil.ignore_patterns('responses.jsonl','__pycache__'))
        for name in ('continuity.py','durable.py'):shutil.copyfile(ROOT/'examples'/name,root/'examples'/name)
        shutil.copyfile(ROOT/'research/verify_reading_transfer.py',root/'research/verify_reading_transfer.py')
        shutil.copyfile(ROOT/'research/audit_reading_transfer.py',root/'research/audit_reading_transfer.py')
        return root

    def invoke(self,root):
        return subprocess.run(['python3','-O',str(root/'research/verify_reading_transfer.py')],text=True,capture_output=True)

    def rewrite(self,root,change,rehash=False):
        here=root/'research/transfer_reading';p=here/'responses.jsonl.gz'
        rows=[json.loads(x) for x in gzip.decompress(p.read_bytes()).splitlines()];change(rows)
        raw=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
        p.write_bytes(gzip.compress(raw,mtime=0))
        if rehash:
            for name in ('completion.json','results.json'):
                target=here/name;d=json.loads(target.read_text());d['raw_sha256']=hashlib.sha256(raw).hexdigest();target.write_text(json.dumps(d))

    def test_original_under_optimization(self):
        r=self.invoke(ROOT);self.assertEqual(r.returncode,0,r.stderr)

    def test_privacy_derivative_document_drift_is_rejected(self):
        root=self.copied();path=root/'research/transfer_reading/THIRD_PARTY_READING.md'
        path.write_text(path.read_text()+'\nchanged license terms\n')
        result=self.invoke(root)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('author-privacy derivative drift',result.stderr)

    def test_changed_privacy_registry_cannot_bless_document_drift(self):
        root=self.copied();path=root/'research/transfer_reading/THIRD_PARTY_READING.md'
        path.write_text(path.read_text()+'\nchanged license terms\n')
        registry=root/'research/transfer_reading/privacy-derivative.json'
        value=json.loads(registry.read_text())
        value['published_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        registry.write_text(json.dumps(value))
        result=self.invoke(root)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unrecognized author-privacy derivative',result.stderr)

    def test_rehashed_preparation_prompt_change_is_rejected(self):
        root=self.copied()
        def change(rows):
            r=next(r for r in rows if r['stage']=='prime')
            r['prompt']+=' altered';r['prompt_sha256']=hashlib.sha256(r['prompt'].encode()).hexdigest()
        self.rewrite(root,change,True)
        r=self.invoke(root);self.assertNotEqual(r.returncode,0);self.assertIn('prompt/history drift',r.stderr)

    def test_rehashed_terminal_reclassification_is_rejected(self):
        root=self.copied()
        self.rewrite(root,lambda rows:rows[0].update(terminal=not rows[0]['terminal']),True)
        r=self.invoke(root);self.assertNotEqual(r.returncode,0);self.assertIn('terminal metadata drift',r.stderr)

    def test_coherently_rehashed_effect_change_is_rejected(self):
        root=self.copied();here=root/'research/transfer_reading'
        target=here/'episodes.json';d=json.loads(target.read_text())
        d['episodes'][0]['primary']=not d['episodes'][0]['primary'];target.write_text(json.dumps(d))
        p=here/'completion.json';meta=json.loads(p.read_text());meta['episodes_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();p.write_text(json.dumps(meta))
        r=self.invoke(root);self.assertNotEqual(r.returncode,0);self.assertIn('episode effect/score drift',r.stderr)

    def test_coherent_cost_rewrite_disagrees_with_native_event(self):
        root=self.copied();changed=[]
        def change(rows):
            row=next(r for r in rows if r['stage']=='prime')
            changed.append(row['arm']);row['usage']['input_tokens']+=7
        self.rewrite(root,change,True)
        target=root/'research/transfer_reading/results.json';result=json.loads(target.read_text())
        next(r for r in result['summary'] if r['arm']==changed[0])['input_tokens']+=7
        target.write_text(json.dumps(result))
        r=self.invoke(root);self.assertNotEqual(r.returncode,0);self.assertIn('native usage metadata drift',r.stderr)


if __name__=='__main__':unittest.main()
