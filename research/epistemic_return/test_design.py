import contextlib
from copy import deepcopy
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from task_design import *
from environment import Environment,persist_memory
from run import reserve,run
from analyze import analyze


def reply(rows,case,observed):
    return {r['id']:{'action':optimum(r,case,observed),'basis':[]} for r in rows}


def fake_inference(prompt):
    """Authored environment-aware test double, never a model result."""
    if prompt=='Use no tools. Return exactly {"ready":true}.':
        answer={'ready':True}
    else:
        data=json.loads(prompt.splitlines()[-1])
        if 'actual_diagnostic' in data:
            case=next(c for c in cases() if c['deployment']==data['tasks'][0]['deployment'])
            observed=data['actual_diagnostic']
            if 'memory is an unrestricted STRING' in prompt:
                memory=json.dumps(observed,separators=(',',':'))
            else:
                memory={'observations':[{'id':e['id'],'deployment':observed['deployment'],
                    'epoch':observed['epoch'],'text':json.dumps(e)} for e in observed['events']],
                    'claims':[],'revisions':[],'limits':['exact deployment and epoch only']}
            answer={'answers':reply(data['tasks'],case,observed),'memory':memory,'reason':'test-double'}
        elif 'saved_memory' in data:
            memory=data['saved_memory']
            if type(memory) is str:observed=json.loads(memory)
            else:
                obs=memory['observations']
                observed={'deployment':obs[0]['deployment'] if obs else '',
                    'epoch':obs[0]['epoch'] if obs else '', 'probe':'sentinel',
                    'events':[json.loads(o['text']) for o in obs]}
            # The test double can identify its case from any exact-match task.
            case=next(c for c in cases() if any(r['deployment']==c['deployment'] and r['epoch']==c['epoch'] for r in data['tasks']))
            answer={'answers':reply(data['tasks'],case,observed),'reason':'test-double'}
        else:
            case=next(c for c in cases() if c['deployment']==data['deployment'])
            answer={'probe':'sentinel','answers':reply(data['tasks'],case,None),'reason':'test-double'}
    return {'response':json.dumps(answer,separators=(',',':')),'terminal':True,'exit_code':0,
            'events':[{'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}],
            'tools':[],'usage':{'input_tokens':1,'output_tokens':1},'wall_ms':1}


class DesignTest(unittest.TestCase):
    def test_identical_start_is_really_indistinguishable(self):
        c=cases()[0];other={**c,'mode':'cache' if c['mode']=='owner' else 'owner','present':False}
        self.assertEqual(initial_prompt(c),initial_prompt(other))
        self.assertNotEqual(diagnostic(c,'sentinel'),diagnostic(other,'sentinel'))

    def test_finite_information_witness_includes_safe_blind_policy(self):
        x=information_witness()
        self.assertEqual(x['best_blind'],14)
        self.assertEqual(x['best_diagnostic'],15.5)
        self.assertEqual(x['best_current_owner_diagnostic'],13.25)
        self.assertEqual(x['blind_expected_utility']['reconcile'],14)
        self.assertEqual(len(x['diagnostic_policies']),6)

    def test_miss_does_not_imply_present(self):
        c=next(c for c in cases() if c['mode']=='cache')
        o=diagnostic(c,'sentinel');r=task(c,'test')
        self.assertEqual(possible(r,c,o),(False,True))
        self.assertEqual(optimum(r,c,o),'reconcile')
        self.assertFalse(justified(r,'confirm',possible(r,c,o)))

    def test_epoch_scope_and_withdrawal_erase_inference_not_history(self):
        c=next(c for c in cases() if c['mode']=='owner');o=diagnostic(c,'sentinel')
        rows={r['id']:r for r in transfer_tasks(c)}
        self.assertEqual(optimum(rows['new-uncertain'],c,o),'retry')
        for key in ('new-epoch','new-deployment','withdrawn-calibration'):
            self.assertEqual(optimum(rows[key],c,o),'reconcile')
        self.assertEqual(o['events'][1]['reply'],'FOUND')

    def test_retention_and_unnecessary_checks_have_cost(self):
        c=cases()[0];rows={r['id']:r for r in transfer_tasks(c)}
        self.assertEqual(optimum(rows['new-found'],c,None),'confirm')
        self.assertEqual(optimum(rows['new-deduplicated'],c,None),'retry')
        self.assertEqual(optimum(rows['expensive-reconciliation'],c,None),'defer')
        self.assertGreater(utility(rows['new-found'],'confirm',True),utility(rows['new-found'],'reconcile',True))

    def test_actual_sqlite_diagnostic_and_effects(self):
        for c in cases():
            with tempfile.TemporaryDirectory() as work:
                rows=source_tasks(c);env=Environment(Path(work)/'world.sqlite',c,rows)
                for p in PROBES:self.assertEqual(env.probe(p),diagnostic(c,p))
                a={'answers':reply(rows,c,diagnostic(c,'sentinel'))}
                effects=env.apply(rows,a,True)
                self.assertTrue(all(not e['bad_effect'] for e in effects))
                for e in effects:
                    self.assertEqual(env.count(e['task']),e['after_count'])

    def test_permitted_unsafe_retry_is_not_silently_guarded_away(self):
        c={**cases()[0],'mode':'cache','present':True};r=task(c,'source-uncertain')
        with tempfile.TemporaryDirectory() as work:
            env=Environment(Path(work)/'world.sqlite',c,[r])
            e=env.apply([r],{'answers':{r['id']:{'action':'retry'}}},True)[0]
            self.assertEqual((e['before_count'],e['after_count'],e['bad_effect']),(1,2,'duplicate'))

    def test_memory_shape_is_not_semantic_truth(self):
        m={'observations':[],'claims':[{'id':'fake','deployment':'d','epoch':'e','text':'invented owner','basis':[], 'status':'certain'}],
           'revisions':[],'limits':[]}
        self.assertEqual(memory_value({'memory':m},'linked_actual'),m)
        self.assertIsNone(knowledge({'probe':'sentinel','events':[]}))
        for bad in [None,{}, {'observations':[1],'claims':[1],'revisions':[],'limits':[]}]:
            self.assertIn('unavailable',memory_value({'memory':bad},'linked_actual'))

    def test_exact_memory_readback_not_prefix(self):
        m='Я пам’ятаю умову '+('x'*1900)
        with tempfile.TemporaryDirectory() as work:
            got,receipt=persist_memory(Path(work)/'memory.sqlite',m)
            self.assertEqual(got,m);self.assertTrue(receipt['reopened'])
        self.assertIn('unavailable',memory_value({'memory':'x'*2049},'free_actual'))

    def test_output_guard_rejects_compressed_only_and_dangling_symlink(self):
        for name,link in [('responses.jsonl.gz',False),('completion.json',True)]:
            with tempfile.TemporaryDirectory() as work:
                folder=Path(work)
                if link:(folder/name).symlink_to(folder/'absent')
                else:(folder/name).write_bytes(b'original')
                with self.assertRaisesRegex(ValueError,'already-started'):reserve(folder)
                self.assertFalse((folder/'run-reservation.json').exists())

    def test_partial_canary_never_retries(self):
        called=[]
        def bad(prompt):called.append(prompt);return {**fake_inference(prompt),'terminal':False}
        with tempfile.TemporaryDirectory() as work,contextlib.redirect_stdout(io.StringIO()):
            folder=Path(work)
            with self.assertRaisesRegex(ValueError,'canary'):run(bad,verify=False,output_dir=folder)
            with self.assertRaisesRegex(ValueError,'already-started'):run(bad,verify=False,output_dir=folder)
            self.assertEqual(len(called),1)
            self.assertEqual(json.loads((folder/'completion.json').read_text())['status'],'partial')

    def test_full_fake_cohort_replay_and_coherent_forgery(self):
        with tempfile.TemporaryDirectory() as work,contextlib.redirect_stdout(io.StringIO()):
            folder=Path(work);run(fake_inference,verify=False,output_dir=folder)
            out=analyze(folder,check_pins=False)
            for a in ARMS:self.assertEqual(out['arms'][a]['transfer_optimal'],80)
            for a in ('free_actual','linked_actual'):
                self.assertEqual(out['arms'][a]['full_information_transfer_optimal'],80)
            for a in ('free_masked','linked_masked'):
                self.assertEqual(out['arms'][a]['full_information_transfer_optimal'],68)
            wire=gzip.decompress((folder/'responses.jsonl.gz').read_bytes())
            rows=[json.loads(x) for x in wire.splitlines()]
            target=next(r for r in rows if r.get('kind')=='runtime')
            target['admitted_memory']='forged'
            wire=b'\n'.join(json.dumps(r).encode() for r in rows)+b'\n'
            (folder/'responses.jsonl.gz').write_bytes(gzip.compress(wire,mtime=0))
            done=json.loads((folder/'completion.json').read_text());done['raw_sha256']=sha(wire)
            (folder/'completion.json').write_text(json.dumps(done))
            with self.assertRaisesRegex(ValueError,'memory-drift'):analyze(folder,check_pins=False)


if __name__=='__main__':unittest.main()
