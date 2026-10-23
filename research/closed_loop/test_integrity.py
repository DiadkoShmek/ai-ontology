"""Full instrument replay with an explicitly AUTHORED no-model adapter.

All files are temporary under ignored build/. These are not research outcomes.
"""
import contextlib
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import analyze
import run
from tasks import RULES,oracle_facts
from participation_method import reference_method


class InstrumentIntegrityTests(unittest.TestCase):
    def test_full_authored_loop_replay_and_coherent_score_forgery(self):
        root=run.ROOT;(root/'build').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='instrument-fixture-',dir=root/'build') as folder:
            base=Path(folder)
            canary=b'{"terminal":true,"response":"{\\"ready\\":true}"}'
            (base/'canary.json').write_bytes(canary)
            frozen={'input_sha256':{},'schedule':run.schedule(),'requested_model':'AUTHORED-TEST-DOUBLE-NOT-LLM',
                    'canary_sha256':hashlib.sha256(canary).hexdigest()}
            (base/'freeze.json').write_text(json.dumps(frozen))
            def authored(prompt):
                data=json.loads(prompt[len(RULES):]);facts,_=oracle_facts(data['current_world'])
                response=json.dumps({'method':reference_method(),**facts,'carry':'authored fixture','reason':'not an LLM response'})
                return {'response':response,'terminal':True,'exit_code':0,'tools':[],
                        'events':[{'type':'turn.completed'}],'usage':{},'wall_ms':0.0}
            with patch.object(run,'HERE',base),patch.object(run,'pins',lambda:{}),patch.object(run,'invoke',authored),contextlib.redirect_stdout(io.StringIO()):
                run.run()
            done=json.loads((base/'completion.json').read_text())
            self.assertEqual(done['calls'],32);self.assertEqual(done['transfer_executions'],768)
            with patch.object(analyze,'pins',lambda:{}):
                report=analyze.analyze(base)
                self.assertEqual([s['complete'] for s in report['summary']],[8,8])
                self.assertTrue(all(r['behavior_changed']==0 for r in report['method_revisions']))
                raw=gzip.decompress((base/'responses.jsonl.gz').read_bytes());rows=[json.loads(x) for x in raw.splitlines()]
                rows[0]['score']['all_correct']=False
                changed=''.join(json.dumps(x)+'\n' for x in rows).encode()
                (base/'responses.jsonl.gz').write_bytes(gzip.compress(changed,mtime=0))
                done['raw_sha256']=hashlib.sha256(changed).hexdigest();(base/'completion.json').write_text(json.dumps(done))
                with self.assertRaisesRegex(ValueError,'score-drift'):analyze.analyze(base)


if __name__=='__main__':unittest.main()
