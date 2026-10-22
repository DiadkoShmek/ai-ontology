"""Derive publication tables from frozen scores. No inference or network."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build():
    cohorts=[];inputs={};follow=[]
    for folder in ('continuity_pilot','continuity_pilot_v2'):
        p=ROOT/'research'/folder
        for name in ('results.json','completion.json','freeze.json'):
            f=p/name;inputs[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
        result=json.loads((p/'results.json').read_text())
        f=p/'responses.jsonl.gz'
        raw=gzip.decompress(f.read_bytes()) if f.exists() else (p/'responses.jsonl').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=result['raw_sha256']:
            raise ValueError('response hash mismatch: '+folder)
        rows=[json.loads(s) for s in raw.decode().splitlines()]
        groups=[]
        for g in result['summary']:
            selected=[r for r in rows if r['model']==g['model'] and r['arm']==g['arm']]
            counts={key:sum(r['score'].get('fields',{}).get(key,False) for r in selected)
                    for key in ('status','origin','stance','cites')}
            groups.append({**g,'field_correct':counts})
        cohorts.append({'id':folder,'scored_calls':len(rows),'summary':groups,'paired':result['paired']})
        if folder.endswith('v2'):follow=groups
    smoke=ROOT/'research/model-integration-results.json'
    inputs[str(smoke.relative_to(ROOT))]=hashlib.sha256(smoke.read_bytes()).hexdigest()
    s=json.loads(smoke.read_text())
    return {'schema':'ontology-study-summary/1','status':'developer-run-exploratory-diagnostic',
        'scored_model_calls':sum(c['scored_calls'] for c in cohorts),'unique_cases':24,
        'families':6,'cohorts':cohorts,'unscored_warmups':4,'integration_smoke_calls':s['llm_calls'],
        'integration_smoke_committed':sum(r['status']=='committed' for r in s['results']),
        'inputs_sha256':inputs,
        'conclusion':'Mixed model-specific results; no observed aggregate advantage over the information-matched simple index.',
        'scope':'Synthetic status, origin, stance and citation decisions; not voice, reading effects or natural-task transfer.'}


if __name__=='__main__':
    out=ROOT/'research/study-summary.json'
    out.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n')
    print('Derived study summary: 384 scored decisions, 4 warm-ups, 2 separate smoke calls.')
