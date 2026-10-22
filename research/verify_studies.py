"""Verify public study bytes, prompts, completion coverage and score derivation.

No inference, network, secrets or Git mutation. Checks internal consistency;
it does not provide an independent timestamp or authenticate an experimenter.
"""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify(folder, object_store):
    p=ROOT/'research'/folder
    freeze=json.loads((p/'freeze.json').read_text())
    result=json.loads((p/'results.json').read_text())
    completion=json.loads((p/'completion.json').read_text())
    zipped=p/'responses.jsonl.gz';plain=p/'responses.jsonl'
    raw=gzip.decompress(zipped.read_bytes()) if zipped.exists() else plain.read_bytes()
    if zipped.exists() and plain.exists():assert raw==plain.read_bytes(),'archive/raw mismatch'
    assert sha(raw)==result['raw_sha256']==completion['response_sha256']
    assert sha((p/'freeze.json').read_bytes())==result['freeze_sha256']
    # The published runtime may contain later repairs. Reconstruct the exact
    # pre-inference bytes in a temporary tree; never substitute current code.
    snapshot=tempfile.TemporaryDirectory()
    source_root=Path(snapshot.name)
    for name,h in freeze['input_sha256'].items():
        source=(ROOT/name).read_bytes()
        if sha(source)!=h:
            source=subprocess.check_output(['git','--git-dir',str(object_store),'show',
                completion['input_commit']+':'+name])
        assert sha(source)==h,name
        dest=source_root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source)
    frozen_path=source_root/'research'/folder
    (frozen_path/'freeze.json').write_bytes((p/'freeze.json').read_bytes())
    (frozen_path/'responses.jsonl').write_bytes(raw)
    cases={x['id']:x for x in json.loads((p/'cases.json').read_text())}
    # Load only our already hash-checked authored module, under an isolated
    # namespace; its import defines functions and makes no model calls.
    import importlib.util
    for key in ('design','continuity','durable'):sys.modules.pop(key,None)
    spec=importlib.util.spec_from_file_location(folder+'_design',frozen_path/'design.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[json.loads(s) for s in raw.decode().splitlines()]
    expected={(m['name'],c,a) for m in freeze['models'] for c in cases for a in freeze['arms']}
    keys=[(r['model'],r['case'],r['arm']) for r in rows]
    assert set(keys)==expected and len(keys)==len(set(keys))==192
    for r in rows:
        case=cases[r['case']]
        assert r['family']==case['family']
        assert r['input_commit']==completion['input_commit']
        assert r['messages']==module.messages(case,r['arm'])
        fmt='json' if folder=='continuity_pilot' else {
            'type':'object','additionalProperties':False,'required':['status','origin','stance','cites'],
            'properties':{'status':{'type':'string','enum':['supported','refuted','hypothesis','unknown','needs-review']},
                'origin':{'type':'string','enum':['self','peer','none']},
                'stance':{'type':'string','enum':['answer','abstain']},
                'cites':{'type':'array','items':{'type':'string'}}}}
        payload={'model':r['model'],'messages':r['messages'],'format':fmt,'stream':False,
                 'options':freeze['options'],'keep_alive':'10m'}
        assert sha(json.dumps(payload,sort_keys=True).encode())==r['request_sha256']
        s=module.score(r.get('response',''),case['gold'])
        s['exact']=bool(s['exact'] and r['terminal'])
        assert s==r['score'],'score field drift'
        if r['terminal']:
            assert r['backend']['model']==r['model'] and r['backend']['done_reason']=='stop'
        assert (r.get('backend',{}).get('prompt_eval_count') or 0)+128 < 8192,'context overflow risk'
    for group in result['summary']:
        selected=[r for r in rows if r['model']==group['model'] and r['arm']==group['arm']]
        assert len(selected)==group['n']==24
        assert sum(r['score']['exact'] for r in selected)==group['correct']
        assert sum(r.get('backend',{}).get('prompt_eval_count') or 0 for r in selected)==group['input_tokens']
    subprocess.run([sys.executable,str(frozen_path/'analyze.py')],check=True,capture_output=True)
    assert json.loads((frozen_path/'results.json').read_text())==result,'registered analysis drift'
    snapshot.cleanup()
    return {'cohort':folder,'calls':len(rows),'raw_sha256':sha(raw),'internally_consistent':True}


if __name__=='__main__':
    with tempfile.TemporaryDirectory() as d:
        objects=Path(d)/'objects.git'
        subprocess.run(['git','init','--bare','--quiet',str(objects)],check=True)
        subprocess.run(['git','--git-dir',str(objects),'fetch','--quiet','--no-tags',
            str(ROOT/'research/continuity-pilot-history.bundle'),'HEAD'],check=True)
        results=[verify(x,objects) for x in ['continuity_pilot','continuity_pilot_v2']]
        from summarize_studies import build
        assert build()==json.loads((ROOT/'research/study-summary.json').read_text()),'derived table drift'
        print(json.dumps(results))
